import datetime
import os
import time
import copy

import torch
import torch.utils.data
from torch import nn
import torchvision
import torch.quantization
import utils
from train import train_one_epoch, evaluate, load_data

from edgeai_modeltools import pt as edgeai_pt_tools
# import edgeai_modeltools.pt.xao.quantization.quant_torch_fx as qat_module
import edgeai_modeltools.pt.xao.quantization.quant_torch_eager as qat_module


def main(args):
    if args.output_dir:
        utils.mkdir(args.output_dir)

    utils.init_distributed_mode(args)
    print(args)

    if args.post_training_quantize and args.distributed:
        raise RuntimeError("Post training quantization example should not be performed "
                           "on distributed mode")

    device = torch.device(args.device)
    torch.backends.cudnn.benchmark = True

    # Data loading code
    print("Loading data")
    train_dir = os.path.join(args.data_path, 'train')
    val_dir = os.path.join(args.data_path, 'val')

    dataset, dataset_test, train_sampler, test_sampler = load_data(train_dir, val_dir, args)

    data_loader = torch.utils.data.DataLoader(
        dataset, batch_size=args.batch_size,
        sampler=train_sampler, num_workers=args.workers, pin_memory=True)

    data_loader_test = torch.utils.data.DataLoader(
        dataset_test, batch_size=args.eval_batch_size,
        sampler=test_sampler, num_workers=args.workers, pin_memory=True)

    print("Creating model", args.model)
    # when training quantized models, we always start from a pre-trained fp32 reference model
    model = torchvision.models.quantization.__dict__[args.model](pretrained=True, quantize=args.test_only)
    # prepare model for quantization
    # pytorch supports varius quantized backends - eg.  'qnnpack', 'fbgemm' (default is fbgemm)
    model = qat_module.prepare(model, backend=None,
        num_batch_norm_update_epochs=args.num_batch_norm_update_epochs,
        num_observer_update_epochs=args.num_observer_update_epochs)
    # use cuda if set
    model.to(device)

    if not (args.test_only or args.post_training_quantize):
        if args.distributed and args.sync_bn:
            model = torch.nn.SyncBatchNorm.convert_sync_batchnorm(model)

        optimizer = torch.optim.SGD(
            model.parameters(), lr=args.lr, momentum=args.momentum,
            weight_decay=args.weight_decay)

        lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer,
                                                       step_size=args.lr_step_size,
                                                       gamma=args.lr_gamma)

    criterion = nn.CrossEntropyLoss()
    model_without_ddp = model
    if args.distributed:
        model = torch.nn.parallel.DistributedDataParallel(model, device_ids=[args.gpu])
        model_without_ddp = model.module
    else:
        model = torch.nn.parallel.DataParallel(model)
        model_without_ddp = model.module

    if args.resume:
        checkpoint = torch.load(args.resume, map_location='cpu')
        model_without_ddp.load_state_dict(checkpoint['model'])
        optimizer.load_state_dict(checkpoint['optimizer'])
        lr_scheduler.load_state_dict(checkpoint['lr_scheduler'])
        args.start_epoch = checkpoint['epoch'] + 1

    if args.test_only:
        qat_module.eval(model)
        evaluate(model, criterion, data_loader_test, device=device)
        return

    start_time = time.time()
    for epoch in range(args.start_epoch, args.epochs):
        if args.distributed:
            train_sampler.set_epoch(epoch)

        print('Starting training for epoch', epoch)
        # put in train() mode and enable observers
        qat_module.train(model)
        # training epoch
        train_one_epoch(model, criterion, optimizer, data_loader, device, epoch,
            print_freq=args.print_freq)

        lr_scheduler.step()
        with torch.no_grad():
            print('Evaluate QAT model with Fake Quant Ops')
            qat_module.eval(model)
            evaluate(model, criterion, data_loader_test, device=device)

            print('Evaluate Quantized Int model')
            quantized_eval_model = qat_module.convert(model_without_ddp)
            evaluate(quantized_eval_model, criterion, data_loader_test, device=torch.device('cpu'))

        if args.output_dir:
            checkpoint = {
                'model': model_without_ddp.state_dict(),
                'eval_model': quantized_eval_model.state_dict(),
                'optimizer': optimizer.state_dict(),
                'lr_scheduler': lr_scheduler.state_dict(),
                'epoch': epoch,
                'args': args}
            utils.save_on_master(
                checkpoint,
                os.path.join(args.output_dir, 'model_{}.pth'.format(epoch)))
            utils.save_on_master(
                checkpoint,
                os.path.join(args.output_dir, 'checkpoint.pth'))
        print('Saving models after epoch ', epoch)

    # onnx export int model
    dummy_input = torch.rand((1, 3, 224, 224)).to('cpu')
    quantized_ts_model = torch.jit.script(quantized_eval_model)
    torch.jit.save(quantized_ts_model, os.path.join(args.output_dir, 'model_int_ts.pt'))
    torch.onnx.export(quantized_eval_model, dummy_input, os.path.join(args.output_dir, 'model_int.onnx'),
                      export_params=True, verbose=False, do_constant_folding=True, opset_version=11)

    total_time = time.time() - start_time
    total_time_str = str(datetime.timedelta(seconds=int(total_time)))
    print('Training time {}'.format(total_time_str))


def get_args_parser(add_help=True):
    import argparse
    parser = argparse.ArgumentParser(description='PyTorch Quantized Classification Training', add_help=add_help)

    parser.add_argument('--data-path',
                        default='./data/datasets/imagenet',
                        help='dataset')
    parser.add_argument('--model',
                        default='mobilenet_v2',
                        help='model')
    parser.add_argument('--backend',
                        default='qnnpack',
                        help='fbgemm or qnnpack')
    parser.add_argument('--device',
                        default='cuda',
                        help='device')

    parser.add_argument('-b', '--batch-size', default=32, type=int,
                        help='batch size for calibration/training')
    parser.add_argument('--eval-batch-size', default=128, type=int,
                        help='batch size for evaluation')
    parser.add_argument('--epochs', default=90, type=int, metavar='N',
                        help='number of total epochs to run')
    parser.add_argument('--num-observer-update-epochs',
                        default=4, type=int, metavar='N',
                        help='number of total epochs to update observers')
    parser.add_argument('--num-batch-norm-update-epochs', default=3,
                        type=int, metavar='N',
                        help='number of total epochs to update batch norm stats')
    parser.add_argument('--num-calibration-batches',
                        default=32, type=int, metavar='N',
                        help='number of batches of training set for \
                              observer calibration ')

    parser.add_argument('-j', '--workers', default=16, type=int, metavar='N',
                        help='number of data loading workers (default: 16)')
    parser.add_argument('--lr',
                        default=0.0001, type=float,
                        help='initial learning rate')
    parser.add_argument('--momentum',
                        default=0.9, type=float, metavar='M',
                        help='momentum')
    parser.add_argument('--wd', '--weight-decay', default=1e-4, type=float,
                        metavar='W', help='weight decay (default: 1e-4)',
                        dest='weight_decay')
    parser.add_argument('--lr-step-size', default=30, type=int,
                        help='decrease lr every step-size epochs')
    parser.add_argument('--lr-gamma', default=0.1, type=float,
                        help='decrease lr by a factor of lr-gamma')
    parser.add_argument('--print-freq', default=100, type=int,
                        help='print frequency')
    parser.add_argument('--output-dir', default='.', help='path where to save')
    parser.add_argument('--resume', default='', help='resume from checkpoint')
    parser.add_argument('--start-epoch', default=0, type=int, metavar='N',
                        help='start epoch')
    parser.add_argument(
        "--cache-dataset",
        dest="cache_dataset",
        help="Cache the datasets for quicker initialization. \
             It also serializes the transforms",
        action="store_true",
    )
    parser.add_argument(
        "--sync-bn",
        dest="sync_bn",
        help="Use sync batch norm",
        action="store_true",
    )
    parser.add_argument(
        "--test-only",
        dest="test_only",
        help="Only test the model",
        action="store_true",
    )
    parser.add_argument(
        "--post-training-quantize",
        dest="post_training_quantize",
        help="Post training quantize the model",
        action="store_true",
    )
    parser.add_argument('--epoch-size', type=float, default=0,
        help='epoch size. options are: 0, fraction or number. '
              '0 will use the full epoch. '
              'using a number will cause the epoch to have that many images. '
              'using a fraction will reduce the number of images used for one epoch. ')

    # distributed training parameters
    parser.add_argument('--world-size', default=1, type=int,
                        help='number of distributed processes')
    parser.add_argument('--dist-url',
                        default='env://',
                        help='url used to set up distributed training')

    return parser


if __name__ == "__main__":
    args = get_args_parser().parse_args()
    main(args)

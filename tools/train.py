# Copyright (c) OpenMMLab. All rights reserved.
import argparse
import os
import os.path as osp
import warnings

from mmengine.config import Config, DictAction
from mmengine.registry import RUNNERS
from mmengine.runner import Runner
from mmengine.model import is_model_wrapper
from mmengine.logging import print_log

from mmdet.utils import setup_cache_size_limit_of_dynamo
import mmdet.hooks
from edgeai_torchmodelopt import xmodelopt

def parse_args():
    parser = argparse.ArgumentParser(description='Train a detector')
    parser.add_argument('config', help='train config file path')
    parser.add_argument('--work-dir', help='the dir to save logs and models')
    parser.add_argument(
        '--amp',
        action='store_true',
        default=False,
        help='enable automatic-mixed-precision training')
    parser.add_argument(
        '--auto-scale-lr',
        action='store_true',
        help='enable automatically scaling LR.')
    parser.add_argument(
        '--resume',
        nargs='?',
        type=str,
        const='auto',
        help='If specify checkpoint path, resume from it, while if not '
        'specify, try to auto resume from the latest checkpoint '
        'in the work directory.')
    parser.add_argument(
        '--cfg-options',
        nargs='+',
        action=DictAction,
        help='override some settings in the used config, the key-value pair '
        'in xxx=yyy format will be merged into config file. If the value to '
        'be overwritten is a list, it should be like key="[a,b]" or key=a,b '
        'It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" '
        'Note that the quotation marks are necessary and that no white space '
        'is allowed.')
    parser.add_argument(
        '--launcher',
        choices=['none', 'pytorch', 'slurm', 'mpi'],
        default='none',
        help='job launcher')
    # When using PyTorch version >= 2.0.0, the `torch.distributed.launch`
    # will pass the `--local-rank` parameter to `tools/train.py` instead
    # of `--local_rank`.
    parser.add_argument('--local_rank', '--local-rank', type=int, default=0)
    parser.add_argument('--model-surgery', type=int, default=0)
    parser.add_argument('--quantization', type=int, default=0)
    args = parser.parse_args()
    if 'LOCAL_RANK' not in os.environ:
        os.environ['LOCAL_RANK'] = str(args.local_rank)

    return args


def main():
    args = parse_args()

    # Reduce the number of repeated compilations and improve
    # training speed.
    setup_cache_size_limit_of_dynamo()

    # load config
    cfg = Config.fromfile(args.config)
    cfg.launcher = args.launcher
    if args.cfg_options is not None:
        cfg.merge_from_dict(args.cfg_options)

    # work_dir is determined in this priority: CLI > segment in file > filename
    if args.work_dir is not None:
        # update configs according to CLI args if args.work_dir is not None
        cfg.work_dir = args.work_dir
    elif cfg.get('work_dir', None) is None:
        # use config filename as default work_dir if cfg.work_dir is None
        cfg.work_dir = osp.join('./work_dirs',
                                osp.splitext(osp.basename(args.config))[0])

    # enable automatic-mixed-precision training
    if args.amp is True:
        cfg.optim_wrapper.type = 'AmpOptimWrapper'
        cfg.optim_wrapper.loss_scale = 'dynamic'

    # enable automatically scaling LR
    if args.auto_scale_lr:
        if 'auto_scale_lr' in cfg and \
                'enable' in cfg.auto_scale_lr and \
                'base_batch_size' in cfg.auto_scale_lr:
            cfg.auto_scale_lr.enable = True
        else:
            raise RuntimeError('Can not find "auto_scale_lr" or '
                               '"auto_scale_lr.enable" or '
                               '"auto_scale_lr.base_batch_size" in your'
                               ' configuration file.')

    # resume is determined in this priority: resume from > auto_resume
    if args.resume == 'auto':
        cfg.resume = True
        cfg.load_from = None
    elif args.resume is not None:
        cfg.resume = True
        cfg.load_from = args.resume

    cfg.quantization = args.quantization

    # build the runner from config
    if 'runner_type' not in cfg:
        # build the default runner
        runner = Runner.from_cfg(cfg)
    else:
        # build customized runner from the registry
        # if 'runner_type' is set in the cfg
        runner = RUNNERS.build(cfg)

    # model surgery
    if args.model_surgery:
        runner._init_model_weights()

        surgery_wrapper = xmodelopt.surgery.v1.convert_to_lite_model if args.model_surgery == 1 \
                     else (xmodelopt.surgery.v2.convert_to_lite_fx if args.model_surgery == 2 else None)

        is_wrapped = False
        if is_model_wrapper(runner.model):
            runner.model = runner.model.module
            is_wrapped = True
        #
        if hasattr(runner.model, 'surgery_init'):
            print_log('wrapping the model to prepare for surgery')
            runner.model = runner.model.surgery_init(surgery_wrapper, total_epochs=runner.max_epochs)
        else:
            # raise RuntimeError(f'surgery_init method is not supported for {type(runner.model)}')
            runner.model.backbone = surgery_wrapper(runner.model.backbone)
            runner.model.neck = surgery_wrapper(runner.model.neck)
            runner.model.bbox_head.head_module = surgery_wrapper(runner.model.bbox_head.head_module)
        #
        if is_wrapped:
            runner.model = runner.wrap_model(runner.cfg.get('model_wrapper_cfg'), runner.model)
        #

    if args.quantization:
        # load the checkpoint before quantization wrapper
        runner.load_or_resume()

        is_wrapped = False
        if is_model_wrapper(runner.model):
            runner.model = runner.model.module
            is_wrapped = True
        #

        if args.quantization == xmodelopt.quantization.QuantizationVersion.QUANTIZATION_V1:
            test_loader = runner.build_dataloader(runner._test_dataloader)
            example_input = next(iter(test_loader))
            runner.model = xmodelopt.quantization.v1.QuantTrainModule(
                runner.model, dummy_input=example_input, total_epochs=runner.max_epochs)
        elif args.quantization == xmodelopt.quantization.QuantizationVersion.QUANTIZATION_V2:
            if hasattr(runner.model, 'quant_init'):
                print_log('wrapping the model to prepare for quantization')
                runner.model = runner.model.quant_init(
                    xmodelopt.quantization.v2.QATFxModule, total_epochs=runner.max_epochs)
            else:
                print_log(
                    f'quant_init method is not supported for {type(runner.model)}. attempting to use the generic wrapper')
                runner.model = xmodelopt.quantization.v2.QATFxModule(runner.model, total_epochs=runner.max_epochs)
            #
        #

        if is_wrapped:
            runner.model = runner.wrap_model(runner.cfg.get('model_wrapper_cfg'), runner.model)
        #

    #print("\n\n model summary : \n",runner.model)
        
    runner.train()


if __name__ == '__main__':
    main()

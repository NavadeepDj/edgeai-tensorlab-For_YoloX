_base_ = [
    '../../configs/_base_/datasets/coco_detection.py',
    '../../configs/_base_/schedules/schedule_1x.py', '../../configs/_base_/default_runtime.py'
]

input_size = 320 
num_classes = 80
img_norm_cfg = dict(mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True)
backbone_type = 'MobileNetV2P5Lite' #'MobileNetV2Lite' #'MobileNetV1Lite'
# mobilenetv2_pretrained = '/data/files/a0508577/work/edgeai-algo/edgeai-modelzoo/models/vision/detection/coco/edgeai-mmdet/ssd_mobilenetp5_lite_320x320_20230404_checkpoint.pth'
mobilenetv2_pretrained = 'https://software-dl.ti.com/jacinto7/esd/modelzoo/latest/models/vision/classification/imagenet1k/edgeai-tv/mobilenet_v2p5_20230201_checkpoint.pth'
mobilenetv1_pretrained='https://software-dl.ti.com/jacinto7/esd/modelzoo/latest/models/vision/classification/imagenet1k/edgeai-tv/mobilenet_v1_20190906_checkpoint.pth'
pretrained=(mobilenetv2_pretrained if backbone_type == 'MobileNetV2P5Lite' else mobilenetv1_pretrained)

backbone_out_channels=(48, 160, 256, 128, 128, 128) if backbone_type == 'MobileNetV2P5Lite' else (512, 1024, 512, 256, 256, 256)
backbone_out_indices = (1, 2, 3, 4)
basesize_ratio_range = (0.1, 0.9)

conv_cfg = None
norm_cfg = dict(type='BN')
convert_to_lite_model = dict(group_size_dw=1, model_surgery=1)

# model settings
data_preprocessor = dict(
    type='DetDataPreprocessor',
    mean=[123.675, 116.28, 103.53],
    std=[58.395, 57.12, 57.375],
    bgr_to_rgb=True,
    pad_size_divisor=1)
model = dict(
    type='SingleStageDetector',
    data_preprocessor=data_preprocessor,
    backbone=dict(
        type=backbone_type,
        strides=(2, 2, 2, 2, 2),
        depth=None,
        with_last_pool=False,
        ceil_mode=True,
        extra_channels=backbone_out_channels[2:],
        out_indices=backbone_out_indices[-2:],
        out_feature_indices=None,
        l2_norm_scale=None,
        ),
    neck=None,
    bbox_head=dict(
        type='SSDHead',
        in_channels=backbone_out_channels,
        num_classes=num_classes,
        conv_cfg=conv_cfg,
        anchor_generator=dict(
            type='SSDAnchorGenerator',
            scale_major=False,
            input_size=input_size,
            basesize_ratio_range=basesize_ratio_range,
            strides=[16, 32, 64, 128, 256, 512],
            ratios=[[2], [2, 3], [2, 3], [2, 3], [2, 3], [2]],
            # ratios=[[2, 3], [2, 3], [2, 3], [2, 3], [2, 3], [2, 3]],
            ),
        bbox_coder=dict(
            type='DeltaXYWHBBoxCoder',
            target_means=[.0, .0, .0, .0],
            target_stds=[0.1, 0.1, 0.2, 0.2])),
    # model training and testing settings
    train_cfg=dict(
        assigner=dict(
            type='MaxIoUAssigner',
            pos_iou_thr=0.5,
            neg_iou_thr=0.5,
            min_pos_iou=0.,
            ignore_iof_thr=-1,
            gt_max_assign_all=False),
        sampler=dict(type='PseudoSampler'),
        smoothl1_beta=1.,
        allowed_border=-1,
        pos_weight=-1,
        neg_pos_ratio=3,
        debug=False),
    test_cfg=dict(
        nms_pre=1000,
        nms=dict(type='nms', iou_threshold=0.45),
        min_bbox_size=0,
        score_thr=0.02,
        max_per_img=200))
env_cfg = dict(cudnn_benchmark=True)

# dataset settings
input_size = 320
train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations', with_bbox=True),
    dict(
        type='Expand',
        mean=data_preprocessor['mean'],
        to_rgb=data_preprocessor['bgr_to_rgb'],
        ratio_range=(1, 4)),
    dict(
        type='MinIoURandomCrop',
        min_ious=(0.1, 0.3, 0.5, 0.7, 0.9),
        min_crop_size=0.3),
    dict(type='Resize', scale=(input_size, input_size), keep_ratio=False),
    dict(type='RandomFlip', prob=0.5),
    dict(
        type='PhotoMetricDistortion',
        brightness_delta=32,
        contrast_range=(0.5, 1.5),
        saturation_range=(0.5, 1.5),
        hue_delta=18),
    dict(type='PackDetInputs')
]
test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='Resize', scale=(input_size, input_size), keep_ratio=False),
    dict(type='LoadAnnotations', with_bbox=True),
    dict(
        type='PackDetInputs',
        meta_keys=('img_id', 'img_path', 'ori_shape', 'img_shape',
                   'scale_factor'))
]
train_dataloader = dict(
    batch_size=24,
    num_workers=4,
    batch_sampler=None,
    dataset=dict(
        _delete_=True,
        type='RepeatDataset',
        times=5,
        dataset=dict(
            type={{_base_.dataset_type}},
            data_root={{_base_.data_root}},
            ann_file='annotations/instances_train2017.json',
            data_prefix=dict(img='train2017/'),
            filter_cfg=dict(filter_empty_gt=True, min_size=32),
            pipeline=train_pipeline)))
val_dataloader = dict(batch_size=8, dataset=dict(pipeline=test_pipeline))
test_dataloader = val_dataloader

# training schedule
max_epochs = 120
train_cfg = dict(max_epochs=max_epochs, val_interval=5)

# learning rate
param_scheduler = [
    dict(
        type='LinearLR', start_factor=0.001, by_epoch=False, begin=0, end=500),
    dict(
        type='CosineAnnealingLR',
        begin=0,
        T_max=max_epochs,
        end=max_epochs,
        by_epoch=True,
        eta_min=0)
]

# optimizer
optim_wrapper = dict(
    type='OptimWrapper',
    optimizer=dict(type='SGD', lr=0.015, momentum=0.9, weight_decay=4.0e-5))

custom_hooks = [
    dict(type='NumClassCheckHook'),
    dict(type='CheckInvalidLossHook', interval=50, priority='VERY_LOW')
]

# NOTE: `auto_scale_lr` is for automatically scaling LR,
# USER SHOULD NOT CHANGE ITS VALUES.
# base_batch_size = (8 GPUs) x (24 samples per GPU)
auto_scale_lr = dict(base_batch_size=192)

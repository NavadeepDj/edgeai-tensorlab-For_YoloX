_base_ = './yolox_tiny_8xb8-300e_coco.py'

# convert_to_lite_model = dict(model_surgery=1)

# model settings
model = dict(
    backbone=dict(deepen_factor=0.33, widen_factor=0.25, use_depthwise=False),
    neck=dict(
        in_channels=[64, 128, 256],
        out_channels=64,
        num_csp_blocks=1,
        use_depthwise=False),
    bbox_head=dict(in_channels=64, feat_channels=64, use_depthwise=False))

_base_ = '../../configs/yolox_tiny_8xb8-300e_coco.py'

# replace complex activation functions with ReLU.
# Also, if needed, regular convolutions can be replaced with depthwise-separable convolutions.
# edgeai_torchmodelopt needs to be installed from edgeai-modeloptimization
convert_to_lite_model = dict(model_surgery=1)

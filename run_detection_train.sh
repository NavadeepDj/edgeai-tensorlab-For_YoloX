#!/usr/bin/env bash

# Copyright (c) 2018-2021, Texas Instruments
# All Rights Reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

######################################################################


# yolox-lite configs - modification of yolox configs in mmdetection
# CONFIG_FILE="configs_edgeailite/yolox/yolox_nano_lite.py"
# CONFIG_FILE="configs_edgeailite/yolox/yolox_tiny_lite.py"
# CONFIG_FILE="configs_edgeailite/yolox/yolox_s_lite.py"
# CONFIG_FILE="configs_edgeailite/yolox/yolox_m_lite.py"
# CONFIG_FILE="configs_edgeailite/yolox/yolox_l_lite.py"
# CONFIG_FILE="configs_edgeailite/yolox/yolox_x_lite.py"

# ultra-small yolox-lite configs - not recommended, unless there is a real need.
# CONFIG_FILE="configs_edgeailite/yolox/yolox_femto_lite.py"
# CONFIG_FILE="configs_edgeailite/yolox/yolox_pico_lite.py"

# centernet-lite config
# CONFIG_FILE="configs/centernet/centernet_r18_8xb16-crop512-140e_coco.py"

# fcos config
# CONFIG_FILE="configs_edgeailite/fcos/fcos_r50-caffe_fpn_bn-head_1x_coco.py"

# efficientdet-lite configs
# CONFIG_FILE="configs_edgeailite/efficientdet/efficientdet_effb0_bifpn_8xb16-crop512-300e_coco.py"
# CONFIG_FILE="configs_edgeailite/efficientdet/efficientdet_effb1_bifpn_8xb16-crop512-300e_coco.py"


CONFIG_FILE="configs_edgeailite/yolox/yolox_s_lite.py"


######################################################################
# Distributed training
##NUM_GPUS=4
##./tools/dist_train.sh ${CONFIG_FILE} ${NUM_GPUS}

######################################################################
# Single GPU training
python tools/train.py ${CONFIG_FILE}

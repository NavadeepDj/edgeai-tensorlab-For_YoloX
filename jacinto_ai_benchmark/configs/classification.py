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

from .. import utils, datasets, preprocess, sessions, postprocess, metrics


def get_configs(settings, work_dir):
    # get the sessions types to use for each model type
    session_type_dict = sessions.convert_session_names_to_types(settings.session_type_dict)
    onnx_session_type = session_type_dict['onnx']
    tflite_session_type = session_type_dict['tflite']
    mxnet_session_type = session_type_dict['mxnet']

    # configs for each model pipeline
    common_cfg = {
        'pipeline_type': settings.pipeline_type,
        'verbose': settings.verbose,
        'run_import': settings.run_import,
        'run_inference': settings.run_inference,
        'calibration_dataset': settings.dataset_cache['imagenet']['calibration_dataset'],
        'input_dataset': settings.dataset_cache['imagenet']['input_dataset'],
        'postprocess': settings.get_postproc_classification()
    }

    common_session_cfg = dict(work_dir=work_dir, target_device=settings.target_device)

    pipeline_configs = {
        #################################################################
        #       ONNX MODELS
        #################jai-devkit models###############################
        # jai-devkit: classification mobilenetv1_224x224 expected_metric: 71.82% top-1 accuracy
        'vcls-10-100-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_onnx(),
            session=onnx_session_type(**common_session_cfg, **settings.session_tvm_dlr_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/jai-pytorch/mobilenet_v1_20190906-171544_opset9.onnx')
        ),
        # jai-devkit: classification mobilenetv2_224x224 expected_metric: 72.13% top-1 accuracy
        'vcls-10-101-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_onnx(),
            session=onnx_session_type(**common_session_cfg, **settings.session_tvm_dlr_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/jai-pytorch/mobilenet_v2_20191224-153212_opset9.onnx')
        ),
        # jai-devkit: classification mobilenetv2_224x224 expected_metric: 72.13% top-1 accuracy, QAT: 71.73%
        'vcls-10-101-8':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_onnx(),
            session=onnx_session_type(**common_session_cfg, **settings.session_tvm_dlr_cfg_qat,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/jai-pytorch/mobilenet_v2_qat-jai_20201213-165307_opset9.onnx')
        ),
        #################torchvision models#########################
        # torchvision: classification shufflenetv2_224x224 expected_metric: 69.36% top-1 accuracy
        'vcls-10-301-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_onnx(),
            session=onnx_session_type(**common_session_cfg, **settings.session_tvm_dlr_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/torchvision/shufflenet_v2_x1.0_opset9.onnx')
        ),
        # torchvision: classification mobilenetv2_224x224 expected_metric: 71.88% top-1 accuracy
        'vcls-10-302-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_onnx(),
            session=onnx_session_type(**common_session_cfg, **settings.session_tvm_dlr_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/torchvision/mobilenet_v2_tv_opset9.onnx')
        ),
        # torchvision: classification mobilenetv2_224x224 expected_metric: 71.88% top-1 accuracy, QAT: 71.31%
        'vcls-10-302-8':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_onnx(),
            session=onnx_session_type(**common_session_cfg, **settings.session_tvm_dlr_cfg_qat,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/torchvision/mobilenet_v2_tv_qat-jai_opset9.onnx')
        ),
        # torchvision: classification resnet18_224x224 expected_metric: 69.76% top-1 accuracy
        'vcls-10-304-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_onnx(),
            session=onnx_session_type(**common_session_cfg, **settings.session_tvm_dlr_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/torchvision/resnet18_opset9.onnx')
        ),
        # torchvision: classification resnet50_224x224 expected_metric: 76.15% top-1 accuracy
        'vcls-10-305-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_onnx(),
            session=onnx_session_type(**common_session_cfg, **settings.session_tvm_dlr_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/torchvision/resnet50_opset9.onnx')
        ),
        # torchvision: classification vgg16_224x224 expected_metric: 71.59% top-1 accuracy - too slow inference
        'vcls-10-306-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_onnx(),
            session=onnx_session_type(**common_session_cfg, **settings.session_tvm_dlr_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/torchvision/vgg16_opset9.onnx')
        ),
        #################pycls regnetx models#########################
        # pycls: classification regnetx200mf_224x224 expected_metric: 68.9% top-1 accuracy
        'vcls-10-030-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_onnx(reverse_channels=True),
            session=onnx_session_type(**common_session_cfg, **settings.session_tvm_dlr_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/pycls/RegNetX-200MF_dds_8gpu_opset9.onnx')
        ),
        # pycls: classification regnetx400mf_224x224 expected_metric: 72.7% top-1 accuracy
        'vcls-10-031-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_onnx(reverse_channels=True),
            session=onnx_session_type(**common_session_cfg, **settings.session_tvm_dlr_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/pycls/RegNetX-400MF_dds_8gpu_opset9.onnx')
        ),
        # pycls: classification regnetx800mf_224x224 expected_metric: 75.2% top-1 accuracy
        'vcls-10-032-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_onnx(reverse_channels=True),
            session=onnx_session_type(**common_session_cfg, **settings.session_tvm_dlr_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/pycls/RegNetX-800MF_dds_8gpu_opset9.onnx')
        ),
        # pycls: classification regnetx1.6gf_224x224 expected_metric: 77.0% top-1 accuracy
        'vcls-10-033-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_onnx(reverse_channels=True),
            session=onnx_session_type(**common_session_cfg, **settings.session_tvm_dlr_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/pycls/RegNetX-1.6GF_dds_8gpu_opset9.onnx')
        ),
        #################github/onnx/models#############################
        # github onnx model: classification resnet18_v2 expected_metric: 69.70% top-1 accuracy
        'vcls-10-020-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_onnx(),
            session=onnx_session_type(**common_session_cfg, **settings.session_tvm_dlr_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/onnx-models/resnet18-v2-7.onnx'),
        ),
        #################################################################
        #       TFLITE MODELS
        ##################tensorflow models##############################
        # mlperf/tf1 model: classification mobilenet_v1_224x224 expected_metric: 71.676 top-1 accuracy
        'vcls-10-010-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/mlperf/mobilenet_v1_1.0_224.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        # mlperf/tf-edge model: classification mobilenet_edgetpu_224 expected_metric: 75.6% top-1 accuracy
        'vcls-10-011-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/mlperf/mobilenet_edgetpu_224_1.0_float.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        # mlperf model: classification resnet50_v1.5 expected_metric: 76.456% top-1 accuracy
        'vcls-10-012-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(mean=(123.675, 116.28, 103.53), scale=(1.0, 1.0, 1.0)),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/mlperf/resnet50_v1.5.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        #########################tensorflow1.0 models##################################
        # tensorflow/models: classification mobilenetv1_224x224 expected_metric: 71.0% top-1 accuracy (or is it 71.676% as this seems same as mlperf model)
        'vcls-10-400-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf1-models/mobilenet_v1_1.0_224.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        # tensorflow/models: classification mobilenetv2_224x224 quant expected_metric: 70.0% top-1 accuracy
        'vcls-10-400-8':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf1-models/mobilenet_v1_1.0_224_quant.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        # tensorflow/models: classification mobilenetv2_224x224 expected_metric: 71.9% top-1 accuracy
        'vcls-10-401-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf1-models/mobilenet_v2_1.0_224.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        # tensorflow/models: classification mobilenetv2_224x224 quant expected_metric: 70.8% top-1 accuracy
        'vcls-10-401-8':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf1-models/mobilenet_v2_1.0_224_quant.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        # tensorflow/models: classification mobilenetv2_224x224 expected_metric: 75.0% top-1 accuracy
        'vcls-10-402-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf1-models/mobilenet_v2_float_1.4_224.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        # tf hosted models: classification squeezenet_1 expected_metric: 49.0% top-1 accuracy
        'vcls-10-403-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(mean=(123.68, 116.78, 103.94), scale=(1/255, 1/255, 1/255)),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf1-models/squeezenet.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        # tf hosted models: classification densenet expected_metric: 74.98% top-1 accuracy (from publication)
        'vcls-10-404-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(mean=(123.68, 116.78, 103.94), scale=(1/255, 1/255, 1/255)),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf1-models/densenet.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        # tf hosted models: classification inception_v1_224_quant expected_metric: 69.63% top-1 accuracy
        'vcls-10-405-8':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf1-models/inception_v1_224_quant.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        # tf hosted models: classification inception_v3 expected_metric: 78% top-1 accuracy
        'vcls-10-406-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(342, 299),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf1-models/inception_v3.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        # tf hosted models: classification mnasnet expected_metric: 74.08% top-1 accuracy
        'vcls-10-407-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf1-models/mnasnet_1.0_224.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        # tf hosted models: classification nasnet mobile expected_metric: 73.9% top-1 accuracy
        'vcls-10-408-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf1-models/nasnet_mobile.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        # tf1 models: classification resnet50_v1 expected_metric: 75.2% top-1 accuracy
        'vcls-10-409-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(mean=(123.675, 116.28, 103.53), scale=(1.0, 1.0, 1.0)),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf1-models/resnet50_v1.tflite')
        ),
        # TODO: is this model's input correct? shouldn't it be 299 according to the slim page?
        # tf1 models: classification resnet50_v2 expected_metric: 75.6% top-1 accuracy
        'vcls-10-410-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf1-models/resnet50_v2.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        #################efficinetnet & tpu models#########################
        # tensorflow/tpu: classification efficinetnet-lite0_224x224 expected_metric: 75.1% top-1 accuracy
        'vcls-10-430-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf-tpu/efficientnet-lite0-fp32.tflite')
        ),
        # tensorflow/tpu: classification efficinetnet-lite1_240x240 expected_metric: 76.7% top-1 accuracy
        'vcls-10-431-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(274, 240),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf-tpu/efficientnet-lite1-fp32.tflite')
        ),
        # tensorflow/tpu: classification efficinetnet-lite2_260x260 expected_metric: 77.6% top-1 accuracy
        'vcls-10-432-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(297, 260),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf-tpu/efficientnet-lite2-fp32.tflite')
        ),
        # tensorflow/tpu: classification efficinetnet-lite4_300x300 expected_metric: 81.5% top-1 accuracy
        'vcls-10-434-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(343, 300),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf-tpu/efficientnet-lite4-fp32.tflite')
        ),
        # tensorflow/tpu: classification efficientnet-edgetpu-S expected_metric: 77.23% top-1 accuracy
        'vcls-10-440-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf-tpu/efficientnet-edgetpu-S_float.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        # tensorflow/tpu: classification efficientnet-edgetpu-M expected_metric: 78.69% top-1 accuracy
        'vcls-10-441-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(274, 240),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf-tpu/efficientnet-edgetpu-M_float.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        # tensorflow/tpu: classification efficientnet-edgetpu-L expected_metric: 80.62% top-1 accuracy
        'vcls-10-442-0':utils.dict_update(common_cfg,
            preprocess=settings.get_preproc_tflite(343, 300),
            session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
                model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf-tpu/efficientnet-edgetpu-L_float.tflite'),
            metric=dict(label_offset_pred=-1)
        ),
        # ##################tf2-models#####################################################
        # # tf2_models: classification xception expected_metric: 79.0% top-1 accuracy
        # 'vcls-10-450-0':utils.dict_update(common_cfg,
        #     preprocess=settings.get_preproc_tflite(342, 299),
        #     session=tflite_session_type(**common_session_cfg, **settings.session_tflite_rt_cfg,
        #         model_path=f'{settings.modelzoo_path}/vision/classification/imagenet1k/tf2-models/xception.tflite')
        # ),
    }
    return pipeline_configs

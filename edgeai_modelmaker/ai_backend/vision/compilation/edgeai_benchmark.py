#################################################################################
# Copyright (c) 2018-2022, Texas Instruments Incorporated - http://www.ti.com
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
#
#################################################################################

import os
import shutil
import jai_benchmark
from .. import utils


class ModelCompilation():
    @classmethod
    def init_params(self, *args, **kwargs):
        params = dict(
            compilation=dict(
            )
        )
        params = utils.ConfigDict(params, *args, **kwargs)
        return params

    def __init__(self, *args, quit_event=None, **kwargs):
        self.params = self.init_params(*args, **kwargs)
        self.quit_event = quit_event
        self.settings_file = jai_benchmark.get_settings_file(target_device=self.params.compilation.target_device, with_model_import=True)
        self.settings = self._get_settings(model_selection=self.params.training.model_id)

    def clear(self):
        # clear the dirs
        shutil.rmtree(self.params.compilation.compilation_path, ignore_errors=True)

    def run(self):
        ''''
        The actual compilation function. Move this to a worker process, if this function is called from a GUI.
        '''
        work_dir, package_dir = self._get_base_dirs()

        if self.params.common.task_type == 'detection':
            dataset_loader = jai_benchmark.datasets.ModelMakerDetectionDataset
        elif self.params.common.task_type == 'classification':
            dataset_loader = jai_benchmark.datasets.ModelMakerClassificationDataset
        else:
            dataset_loader = None
        #

        # can use any suitable data loader provided in datasets folder of edgeai-benchmark or write another
        calib_dataset = dataset_loader(
            path=self.params.dataset.dataset_path,
            split='train',
            shuffle=True,
            num_frames=self.params.compilation.calibration_frames) # num_frames is not critical here
        val_dataset = dataset_loader(
            path=self.params.dataset.dataset_path,
            split='val',
            shuffle=False, # can be set to True as well, if needed
            num_frames=self.params.compilation.num_frames) # this num_frames is important for accuracy calculation

        # it may be easier to get the existing config and modify the aspects that need to be changed
        pipeline_configs = jai_benchmark.tools.select_configs(self.settings, work_dir)
        num_pipeline_configs = len(pipeline_configs)
        assert num_pipeline_configs == 1, f'specify a unique model name in edgeai-benchmark. found {num_pipeline_configs} configs'
        pipeline_configs0 = list(pipeline_configs.values())[0]
        # dataset settings
        pipeline_configs0['calibration_dataset'] = calib_dataset
        pipeline_configs0['input_dataset'] = val_dataset
        # preprocess
        preprocess = pipeline_configs0['preprocess']
        preprocess.set_input_size(resize=self.params.training.input_resize, crop=self.params.training.input_cropsize)
        # session
        pipeline_configs0['session'].set_param('work_dir', work_dir)
        pipeline_configs0['session'].set_param('target_device', self.settings.target_device)
        pipeline_configs0['session'].set_param('model_path', self.params.training.model_export_path)
        # reset - will change based on the model_path given here
        pipeline_configs0['session'].set_param('run_dir', None)
        runtime_options = pipeline_configs0['session'].get_param('runtime_options')
        meta_layers_names_list = 'object_detection:meta_layers_names_list'
        if meta_layers_names_list in runtime_options:
            runtime_options[meta_layers_names_list] = self.params.training.model_proto_path
        #
        runtime_options.update(self.params.compilation.get('runtime_options', {}))
        # the metric reference defined in benchmark code is for the pretrained model - remove it.
        metric_reference = pipeline_configs0['model_info']['metric_reference']
        for k, v in metric_reference.items():
            metric_reference[k] = None # TODO: get from training
        #
        # run the accuracy pipeline
        jai_benchmark.tools.run_accuracy(self.settings, work_dir, pipeline_configs)
        self.params.compiled_path = self._get_output_file()
        return self.params

    def _get_settings(self, model_selection=None):
        runtime_options = dict(accuracy_level=self.params.compilation.accuracy_level)
        settings = jai_benchmark.config_settings.ConfigSettings(
                        self.settings_file,
                        model_selection=model_selection,
                        modelartifacts_path=self.params.compilation.compilation_path,
                        tensor_bits=self.params.compilation.tensor_bits,
                        calibration_frames=self.params.compilation.calibration_frames,
                        calibration_iterations=self.params.compilation.calibration_iterations,
                        num_frames=self.params.compilation.num_frames,
                        runtime_options=runtime_options,
                        parallel_devices=None,
                        dataset_loading=False,
                        save_output=True)
        return settings

    def _get_output_file(self):
        work_dir, package_dir = self._get_base_dirs()
        if not os.path.exists(work_dir):
            return None
        #
        # at the end of model compilation the param.yaml is written
        # so check for it to see if model compilation is complete
        compiled_folder = self._get_log_dir(package_folder=False)
        compiled_package_file = self._get_log_dir(package_folder=True)
        if compiled_folder and not compiled_package_file:
            jai_benchmark.tools.package_artifacts(self.settings, work_dir, out_dir=package_dir)
            compiled_package_file = self._get_log_dir(package_folder=True)
        #
        return compiled_package_file

    def _get_log_dir(self, package_folder=False):
        model_name = self.params.training.model_name
        work_dir, package_dir = self._get_base_dirs()
        if not os.path.exists(work_dir):
            return None
        #
        check_dir = package_dir if package_folder else work_dir
        if not os.path.exists(check_dir):
            return None
        #
        log_dirs = os.listdir(check_dir)
        log_dirs = [l for l in log_dirs if model_name in l]
        if len(log_dirs) == 0:
            return None
        #
        log_dir = log_dirs[0]
        log_dir = os.path.join(check_dir, log_dir)
        if not package_folder:
            # presence of param.yaml indicates that model compilation is complete
            param_yaml = os.path.join(log_dir, 'param.yaml')
            return log_dir if os.path.exists(param_yaml) else None
        else:
            return log_dir

    def _has_logs(self):
        log_dir = self._get_log_dir()
        if (log_dir is None) or (not os.path.exists(log_dir)):
            return False
        #
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        if len(log_files) == 0:
            return False
        #
        return True

    def _get_base_dirs(self):
        work_dir = os.path.join(self.settings.modelartifacts_path, 'modelartifacts', f'{self.settings.tensor_bits}bits')
        package_dir = os.path.join(f'{self.settings.modelartifacts_path}', 'modelartifacts_package', f'{self.settings.tensor_bits}bits')
        return work_dir, package_dir

    def get_params(self):
        return self.params

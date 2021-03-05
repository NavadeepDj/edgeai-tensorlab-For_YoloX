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

import functools
import itertools
import warnings
from .accuracy_pipeline import *
from .. import utils


class PipelineRunner():
    def __init__(self, settings, pipeline_configs):
        self.settings = settings
        for model_id, pipeline_config in pipeline_configs.items():
            # set model_id in each config
            pipeline_config['session'].set_param('model_id', model_id)
            session = pipeline_config['session']
            # call initialize() on each pipeline_config so that run_dir,
            # artifacts folder and such things are initialized
            session.initialize()
        #
        # short list a set of models based on the wild card given in model_selection
        pipelines_selected = {}
        for model_id, pipeline_config in pipeline_configs.items():
            if self._check_model_selection(self.settings, pipeline_config):
                pipelines_selected.update({model_id: pipeline_config})
            #
        #
        if settings.config_range is not None:
            pipelines_selected = dict(itertools.islice(pipelines_selected.items(), *settings.config_range))
        #
        self.pipeline_configs = pipelines_selected

    def run(self):
        if self.settings.parallel_devices is not None:
            return self._run_pipelines_parallel()
        else:
            return self._run_pipelines_sequential()
        #

    def _run_pipelines_sequential(self):
        # get the cwd so that we can continue even if exception occurs
        cwd = os.getcwd()
        results_list = []
        total = len(self.pipeline_configs)
        for pipeline_id, pipeline_config in enumerate(self.pipeline_configs.values()):
            os.chdir(cwd)
            description = f'{pipeline_id+1}/{total}'
            result = self._run_pipeline(self.settings, pipeline_config, description=description)
            results_list.append(result)
        #
        return results_list

    def _run_pipelines_parallel(self):
        # get the cwd so that we can continue even if exception occurs
        cwd = os.getcwd()
        num_devices = len(self.settings.parallel_devices) if self.settings.parallel_devices is not None else 0
        description = 'TASKS'
        parallel_exec = utils.ParallelRun(num_processes=num_devices, desc=description)
        for pipeline_index, pipeline_config in enumerate(self.pipeline_configs.values()):
            os.chdir(cwd)
            parallel_device = self.settings.parallel_devices[pipeline_index % num_devices] \
                if self.settings.parallel_devices is not None else 0
            run_pipeline_bound_func = functools.partial(self._run_pipeline, self.settings, pipeline_config,
                                                        parallel_device=parallel_device, description='')
            parallel_exec.enqueue(run_pipeline_bound_func)
        #
        results_list = parallel_exec.run()
        return results_list

    # this function cannot be an instance method of PipelineRunner, as it causes an
    # error during pickling, involved in the launch of a process is parallel run. make it classmethod
    @classmethod
    def _run_pipeline(cls, settings, pipeline_config, parallel_device=None, description=''):
        if parallel_device is not None:
            os.environ['CUDA_VISIBLE_DEVICES'] = str(parallel_device)
        #
        result = {}
        pipeline_types = utils.as_list(pipeline_config['pipeline_type'])
        try:
            for pipeline_type in pipeline_types:
                if pipeline_type == constants.PIPELINE_ACCURACY:
                    # use with statement, so that the logger and other file resources are cleaned up
                    with AccuracyPipeline(settings, pipeline_config) as accuracy_pipeline:
                        accuracy_result = accuracy_pipeline.run(description)
                        result.update(accuracy_result)
                    #
                elif pipeline_type == constants.PIPELINE_SOMETHING:
                    # this is just an example of how other pipelines can be implemented.
                    # 'something' used here is not real and it is not supported
                    with SomethingPipeline(settings, pipeline_config) as something_pipeline:
                        something_result = something_pipeline.run()
                        result.update(something_result)
                    #
                else:
                    assert False, f'unknown pipeline: {pipeline_type}'
                #
        except Exception as e:
            print(f'\n{str(e)}')
        #
        return result

    def _check_model_selection(self, settings, pipeline_config):
        model_path = pipeline_config['session'].get_param('model_path')
        model_id = pipeline_config['session'].get_param('model_id')
        if settings.model_selection is not None:
            selected_model = False
            model_selection = utils.as_list(settings.model_selection)
            for keyword in model_selection:
                if keyword in model_path:
                    selected_model = True
                #
                if keyword in model_id:
                    selected_model = True
                #
            #
        else:
            selected_model = True
        #
        if settings.model_exclusion is not None:
            model_exclusion = utils.as_list(settings.model_exclusion)
            for keyword in model_exclusion:
                if keyword in model_path:
                    selected_model = False
                #
                if keyword in model_id:
                    selected_model = False
                #
            #
        #
        calibration_dataset = pipeline_config['calibration_dataset']
        if settings.run_import and calibration_dataset is None:
            warnings.warn(f'settings.run_import was set, but calibration_dataset={calibration_dataset}, removing model {model_id}:{model_path}')
            selected_model = False
        #
        input_dataset = pipeline_config['input_dataset']
        if settings.run_inference and input_dataset is None:
            warnings.warn(f'settings.run_inference was set, but input_dataset={input_dataset}, removing model {model_id}:{model_path}')
            selected_model = False
        #
        return selected_model


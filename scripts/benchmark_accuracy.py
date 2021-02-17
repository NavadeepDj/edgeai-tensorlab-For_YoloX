import os
from jacinto_ai_benchmark import *

# the cwd must be the root of the respository
if os.path.split(os.getcwd())[-1] == 'scripts':
    os.chdir('../')
#
# make sure current directory is visible for python import
if not os.environ['PYTHONPATH'].startswith(':'):
    os.environ['PYTHONPATH'] = ':' + os.environ['PYTHONPATH']
#

import config_settings as settings

work_dir = os.path.join('./work_dirs', os.path.splitext(os.path.basename(__file__))[0], f'{settings.tidl_tensor_bits}bits')
print(f'work_dir = {work_dir}')

################################################################################################
# execute each model
if __name__ == '__main__':
    pipeline_configs = {}
    pipeline_configs.update(configs.classification.get_configs(settings, work_dir))
    pipeline_configs.update(configs.detection.get_configs(settings, work_dir))
    pipeline_configs.update(configs.segmentation.get_configs(settings, work_dir))

    if settings.run_import or settings.run_inference:
        pipelines.run(settings, pipeline_configs, parallel_devices=settings.parallel_devices)
    #
    if settings.collect_results:
        results = pipelines.collect_results(settings, work_dir)
        print(*results, sep='\n')
    #


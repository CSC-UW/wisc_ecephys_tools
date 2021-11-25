#TODO remove
import yaml
import os.path

MODULE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
ANALYSIS_PARAMS_PATH = os.path.join(MODULE_DIRECTORY, 'analysis_parameters.yml')

def get_analysis_params(analysis_type, analysis_name):
    with open(ANALYSIS_PARAMS_PATH, 'r') as f:
        return yaml.load(f, Loader=yaml.SafeLoader)[analysis_type][analysis_name]
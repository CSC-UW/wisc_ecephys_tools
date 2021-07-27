import os
from ecephys.data_mgmt import paths

MODULE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
YAML_PATH = os.path.join(MODULE_DIRECTORY, "paths.yaml")


def get_sglx_style_datapaths(subject, experiment, condition, ext):
    return paths.get_sglx_style_datapaths(
        YAML_PATH, subject, experiment, condition, ext
    )


def get_datapath(file, subject, experiment, condition=None):
    return paths.get_datapath(YAML_PATH, file, subject, experiment, condition)
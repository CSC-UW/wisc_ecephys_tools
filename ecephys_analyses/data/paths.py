import os
from ecephys.data import paths

MODULE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(MODULE_DIRECTORY, "datapaths.csv")
YAML_PATH = os.path.join(MODULE_DIRECTORY, "datapaths.yaml")


def get_datapath_from_csv(**kwargs):
    return paths.get_datapath_from_csv(CSV_PATH, **kwargs)


def get_sglx_style_datapaths(subject, experiment, condition, ext):
    return paths.get_sglx_style_datapaths(
        YAML_PATH, subject, experiment, condition, ext
    )


def get_datapath(file, subject, experiment, condition=None):
    return paths.get_datapath(YAML_PATH, file, subject, experiment, condition)
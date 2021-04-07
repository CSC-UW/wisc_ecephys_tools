import os
from ecephys.data import paths
import yaml

MODULE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(MODULE_DIRECTORY, "datapaths.csv")
YAML_PATH = os.path.join(MODULE_DIRECTORY, "datapaths.yaml")


def get_datapath_from_csv(**kwargs):
    return paths.get_datapath_from_csv(CSV_PATH, **kwargs)


def get_sglx_style_datapaths(subject, condition, ext, **kwargs):
    return paths.get_sglx_style_datapaths(YAML_PATH, subject, condition, ext, **kwargs)


def get_datapath(subject, condition, file, **kwargs):
    return paths.get_datapath(YAML_PATH, subject, condition, file, **kwargs)

def get_bin_meta(subject, condition, catgt_data=False):
    return (
        get_sglx_style_datapaths(
            subject,
            condition,
            'ap.bin',
            catgt_data=catgt_data,
        ),
        get_sglx_style_datapaths(
            subject,
            condition,
            'ap.meta',
            catgt_data=catgt_data,
        ),
    )

def get_conditions(subject, condition_group):
    with open(
        os.path.join(MODULE_DIRECTORY, 'conditions.yml'),
        'r'
    ) as f:
        return yaml.load(f, Loader=yaml.SafeLoader)[subject][condition_group]

def load_datapath_yaml():
    with open( YAML_PATH, 'r' ) as f:
        return yaml.load(f, Loader=yaml.SafeLoader)
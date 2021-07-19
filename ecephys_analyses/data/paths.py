import os
from pathlib import Path

import yaml
from ecephys.data import paths

from .channel_groups import full_names


MODULE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(MODULE_DIRECTORY, "datapaths.csv")
YAML_PATH = os.path.join(MODULE_DIRECTORY, "datapaths.yaml")

HYPNO_ROOT = Path('/Volumes/neuropixel/Data/')


def get_subconditions(subject, combined_condition):
    with open(YAML_PATH, 'r') as f:
        datapaths = yaml.safe_load(f)
    subconditions = datapaths[subject][combined_condition]
    if not is_combined_condition(subject, combined_condition):
        raise ValueError(
            f"{combined_condition} doesn't have subconditons for {subject}"
        )
    return subconditions


def is_combined_condition(subject, condition):
    with open(YAML_PATH, 'r') as f:
        datapaths = yaml.safe_load(f)
    subconditions = datapaths[subject][condition]
    return (
        isinstance(subconditions, list)
        and all([subc in datapaths[subject] for subc in subconditions])
    )


def get_hypno_datapaths(subject, condition):
    subject_root = HYPNO_ROOT/full_names[subject]
    return paths.get_sglx_style_datapaths(
        YAML_PATH, subject, condition, 'hypnogram.txt', data_root=subject_root,
    )


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
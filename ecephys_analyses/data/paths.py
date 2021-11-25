#TODO Remove
import os
from pathlib import Path

import yaml
from ecephys.data_mgmt import paths

from .channel_groups import full_names


MODULE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DATAPATHS_CSV_PATH = os.path.join(MODULE_DIRECTORY, "datapaths.csv")
DATAPATHS_YAML_PATH = os.path.join(MODULE_DIRECTORY, "datapaths.yml")

ROOTS_YAML_PATH = os.path.join(MODULE_DIRECTORY, "roots.yml")


def get_subconditions(subject, combined_condition):
    with open(DATAPATHS_YAML_PATH, 'r') as f:
        datapaths = yaml.safe_load(f)
    subconditions = datapaths[subject][combined_condition]
    if not is_combined_condition(subject, combined_condition):
        raise ValueError(
            f"{combined_condition} doesn't have subconditons for {subject}"
        )
    return subconditions


def is_combined_condition(subject, condition):
    with open(DATAPATHS_YAML_PATH, 'r') as f:
        datapaths = yaml.safe_load(f)
    subconditions = datapaths[subject][condition]
    return (
        isinstance(subconditions, list)
        and all([subc in datapaths[subject] for subc in subconditions])
    )


def get_hypno_datapaths(subject, condition):
    with open(ROOTS_YAML_PATH, 'r') as f:
        roots = yaml.safe_load(f)
    assert 'hypno' in roots
    hypno_root = Path(roots['hypno'])
    subject_root = hypno_root/full_names[subject]
    return paths.get_sglx_style_datapaths(
        DATAPATHS_YAML_PATH, subject, condition, 'hypnogram.txt', data_root=subject_root,
    )


def get_subject_root(subject, root_key):
    if root_key is None:
        return None
    with open( ROOTS_YAML_PATH, 'r' ) as f:
        return Path(
            yaml.load(f, Loader=yaml.SafeLoader)[root_key]
        )/full_names[subject]


def get_datapath_from_csv(**kwargs):
    return paths.get_datapath_from_csv(DATAPATHS_CSV_PATH, **kwargs)


def get_catgt_style_datapaths(subject, condition, ext, root_key=None, **kwargs):
    assert root_key is None or root_key == 'catgt'
    root_key = 'catgt'
    data_root = get_subject_root(subject, root_key)
    return paths.get_sglx_style_datapaths(
        DATAPATHS_YAML_PATH,
        subject,
        condition,
        ext,
        catgt_data=True,
        data_root=data_root,
        **kwargs
    )


def get_sglx_style_datapaths(subject, condition, ext, root_key=None, catgt_data=None, **kwargs):
    if catgt_data:
        # Backwards compatibility
        return get_catgt_style_datapaths(subject, condition, ext, root_key=root_key)
    assert root_key != 'catgt'
    data_root = get_subject_root(subject, root_key) if root_key is not None else None
    return paths.get_sglx_style_datapaths(
        DATAPATHS_YAML_PATH,
        subject,
        condition,
        ext,
        catgt_data=False,
        data_root=data_root,
        **kwargs
    )


def get_datapath(subject, condition, file, root_key=None, **kwargs):
    data_root = get_subject_root(subject, root_key) if root_key is not None else None
    return paths.get_datapath(
        DATAPATHS_YAML_PATH,
        subject,
        condition,
        file,
        data_root=data_root,
        **kwargs
    )


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
    with open( DATAPATHS_YAML_PATH, 'r' ) as f:
        return yaml.load(f, Loader=yaml.SafeLoader)
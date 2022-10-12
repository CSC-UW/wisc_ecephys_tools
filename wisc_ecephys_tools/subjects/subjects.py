import os
import yaml
import numpy as np

DEFAULT_SUBJECTS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def get_subjects_directory():
    return DEFAULT_SUBJECTS_DIRECTORY


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def load_yaml_doc(yaml_path):
    """Load a YAML file that contains only one document."""
    with open(yaml_path) as fp:
        yaml_doc = yaml.safe_load(fp)
    return yaml_doc


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_subject_file(subject, subjects_dir=DEFAULT_SUBJECTS_DIRECTORY):
    if subjects_dir is None:
        subjects_dir = DEFAULT_SUBJECTS_DIRECTORY
    return os.path.join(subjects_dir, f"{subject}.yml")


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_subject_doc(subject):
    return load_yaml_doc(get_subject_file(subject))


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_channels(subject, experiment, probe, group, asarray=True):
    doc = get_subject_doc(subject)
    chans = doc["experiments"][experiment]["probes"][probe][group]
    return np.asarray(chans) if asarray else chans


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_depths(subject, experiment, probe, region):
    doc = get_subject_doc(subject)
    return doc["experiments"][experiment]["probes"][probe][region]


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_regions(subject, experiment, probe):
    doc = get_subject_doc(subject)
    return doc["experiments"][experiment]["probes"][probe]

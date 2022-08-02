import os
import numpy as np
from .utils import load_yaml_doc

PACKAGE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
SUBJECTS_DIRECTORY = os.path.join(PACKAGE_DIRECTORY, "subjects")


def get_subject_file(subject_name, subjects_dir=None):
    if subjects_dir is None:
        subjects_dir = SUBJECTS_DIRECTORY
    return os.path.join(subjects_dir, f"{subject_name}.yml")


def get_channels(subject, experiment, probe, group, asarray=True):
    doc = load_yaml_doc(get_subject_file(subject))
    chans = doc["experiments"][experiment]["probes"][probe][group]
    return np.asarray(chans) if asarray else chans


def get_depths(subject, experiment, probe, region):
    doc = load_yaml_doc(get_subject_file(subject))
    return doc["experiments"][experiment]["probes"][probe][region]


def get_regions(subject, experiment, probe):
    doc = load_yaml_doc(get_subject_file(subject))
    return doc["experiments"][experiment]["probes"][probe]

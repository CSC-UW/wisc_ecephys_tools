import os
import yaml
import numpy as np

DEFAULT_SUBJECTS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def get_subjects_directory():
    return DEFAULT_SUBJECTS_DIRECTORY
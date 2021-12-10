# TODO Remove

import os.path

import numpy as np
import yaml
from ecephys.sglx import get_xy_coords

MODULE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
NOISE_CONTAM_PATH = os.path.join(MODULE_DIRECTORY, "noise_contaminated.yml")


def get_noise_contam_dict():
    with open(NOISE_CONTAM_PATH, 'r') as f:
         return yaml.load(f, yaml.SafeLoader)
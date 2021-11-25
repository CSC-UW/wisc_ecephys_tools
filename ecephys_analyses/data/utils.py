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


def depth_from_channel(metapath, ch_indices):
    """Phy depth (from tip of probe) from channel idx.
    
    Args:
        ch_indices: 1-indexed index of channel of interest, ordered
            by location on probe (1 is closest to tip)
    """
    _, _, ycoord = get_xy_coords(metapath)
    sorted_y = sorted(ycoord)
    for i, d in enumerate(sorted_y):
        print(i + 1, d)
    assert all([i > 0 for i in ch_indices]), '1-indexed pls'
    return [
        (idx, np.array(sorted_y)[idx - 1]) for idx in ch_indices
    ]

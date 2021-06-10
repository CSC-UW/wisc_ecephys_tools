from ecephys.sglx_utils import get_xy_coords
import numpy as np


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
    return np.array(sorted_y)[np.array(ch_indices) - 1]
    
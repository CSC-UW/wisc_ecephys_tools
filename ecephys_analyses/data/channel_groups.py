import os.path

import numpy as np
import yaml
from ecephys.neuropixels import checkerboard_map, long_column_map

MODULE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
REGION_YAML_PATH = os.path.join(MODULE_DIRECTORY, "regions.yml")

CheckPat = checkerboard_map.get_user_order()
LongCol = long_column_map.get_user_order()

full_names = {
    'Alessandro': 'CNPIX5-Alessandro',
    'Allan': 'CNPIX8-Allan',
    'Doppio': 'CNPIX4-Doppio',
    'Eugene': 'CNPIX6-Eugene',
    'Giuseppe': 'CNPIX7-Giuseppe',
    'Luigi': 'CNPIX9-Luigi',
    'Charles': 'CNPIX10-Charles',
    'Segundo': 'CNPIX2-Segundo',
    'Adrian': 'CNPIX11-Adrian',
}

full = {
    "Segundo": LongCol,
    "Valentino": CheckPat,
    "Doppio": CheckPat,
    "Alessandro": LongCol,
    "Eugene": LongCol,
}

# This list is incomplete
bad = {"Segundo": [191]}

emg = {
    "Segundo": LongCol[0:-1:191],  # "LF0;384", "LF382;766", "LF381;765"
    "Valentino": CheckPat[0:-1:191],  # "LF0;384", "LF383;767", "LF381;765"
    "Doppio": CheckPat[0:-1:191],  # "LF0;384", "LF383;767", "LF381;765"
    "Alessandro": LongCol[0:-1:191],  # "LF0;384", "LF382;766", "LF381;765"
    "Eugene": LongCol[0:-1:191],  # "LF0;384", "LF382;766", "LF381;765"
}

# Visually identified in the LFP
stratum_pyrmidale_inversion = {
    "Segundo": [175],
    "Valentino": [185],  # Maybe also 1 channel more dorsal
    "Doppio": [166],  # Maybe also 1 channel more dorsal
    "Alessandro": [165],  # Maybe also 1 channel more dorsal
    "Eugene": [203],
}

superficial_ctx = {
    "Segundo": [375, 377, 379, 381, 383],
    "Valentino": [374, 377, 378, 381, 382],
    "Doppio": [374, 377, 378, 381, 382],
    "Alessandro": [375, 377, 379, 381, 383],
    "Eugene": [375, 377, 379, 381, 383],
}

# Identified on the basis of whole-probe CSD from during recovery sleep.
hippocampus = {
    "Segundo": LongCol[213:301],  # 4.25mm to 6.00mm from probe tip
    "Valentino": CheckPat[190:305],  # 3.8mm to 6.1mm from probe tip
    "Doppio": CheckPat[190:291],  # 3.8mm to 5.8mm from probe tip
    "Alessandro": LongCol[190:291],  # 3.8mm to 5.8mm from probe tip
    "Eugene": LongCol[240:311],  # 4.8mm to 6.2mm from probe tip
}

# All channels 140um to 200um ventral to the CA1 stratum pyramidale inversion.
stratum_radiatum_140um_to_200um = {
    "Segundo": [155, 157, 159, 161],
    "Valentino": [165, 166, 169, 170],
    "Doppio": [146, 149, 150, 153],
    "Alessandro": [145, 147, 149, 151],
    "Eugene": [183, 185, 187, 189],
}

drift_tracking = {"Valentino": CheckPat[180:320]}

# Depths intervals for each region,
# NB: As in Phy, depth is ycoord measured from tip of probe,
# so deepest channel may have depth > 0
with open(REGION_YAML_PATH, 'r') as f:
    region_depths = yaml.load(f, Loader=yaml.SafeLoader)

def get_regions(subject, condition, regions_list, depths_list):
    regions_dict = region_depths[subject][condition]
    # TODO: Check that no overlapping regions
    res = np.array([None for _ in depths_list])
    for region, depths in {r: regions_dict.get(r, [-999, -999]) for r in regions_list}.items():
        idx = [d >= depths[0] and d <= depths[1] for d in depths_list]
        res[idx] = region
    return res

# stratum_radiatum = {"Doppio": CheckPat[260:273]}  # LF137 through LF161
# stratum_oriens_100um = {"Doppio": [177]}
# ripple_detection = {
#     "Segundo": [163, 165, 167, 169, 171, 173, 175, 177, 179, 181, 183],
#     "Valentino": [162, 165, 166, 169, 170, 173, 174, 177, 178, 181, 182],
#     "Doppio": [161, 162, 165, 166, 169, 170, 173, 174, 177, 178, 181],
#     "Alessandro": [159, 161, 163, 165, 167, 169, 171, 173, 175, 177, 179],
#     "Eugene": [193, 195, 197, 199, 201, 203, 205, 207, 209, 211],
# }

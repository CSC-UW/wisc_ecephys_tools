import numpy as np
from ecephys.neuropixels import checkerboard_map, long_column_map

CheckPat = checkerboard_map.get_user_order()
LongCol = long_column_map.get_user_order()

full = {
    "Segundo": LongCol,
    "Valentino": CheckPat,
    "Doppio": CheckPat,
    "Alessandro": LongCol,
    "Eugene": LongCol,
    "Allan": np.concatenate([LongCol[41:], (LongCol[0:41])]),
}

# This list is incomplete
bad = {"Segundo": [191]}

emg = {
    "Segundo": LongCol[0:-1:191],  # "LF0;384", "LF382;766", "LF381;765"
    "Valentino": CheckPat[0:-1:191],  # "LF0;384", "LF383;767", "LF381;765"
    "Doppio": CheckPat[0:-1:191],  # "LF0;384", "LF383;767", "LF381;765" on imec0 (mpta)
    "Alessandro": LongCol[0:-1:191],  # "LF0;384", "LF382;766", "LF381;765"
    "Eugene": LongCol[0:-1:191],  # "LF0;384", "LF382;766", "LF381;765"
    "Giuseppe": [10, 328, 275],  # LF10;394, LF328;712, LF275;659 on imec0
    "Allan": [82, 75, 70],  # LF82;466, LF75;459, LF70;454 on imec1
    # "Allan": [0, 328, 275],  # "LF0;384", "LF328;712", "LF275;659" on imec0 (frontal)
}

# Visually identified in the LFP during the first 2h of recovery sleep
stratum_pyrmidale_inversion = {
    "Segundo": [175],
    "Valentino": [185],  # Maybe also 1 channel more dorsal
    "Doppio": [166],  # Maybe also 1 channel more dorsal
    "Alessandro": [165],  # Maybe also 1 channel more dorsal
    "Eugene": [203],
    "Allan": [231],
}

superficial_ctx = {
    "Segundo": [375, 377, 379, 381, 383],
    "Valentino": [374, 377, 378, 381, 382],
    "Doppio": [374, 377, 378, 381, 382],
    "Alessandro": [375, 377, 379, 381, 383],
    "Eugene": [375, 377, 379, 381, 383],
    "Allan": [72, 74, 76, 78, 80],
}

# Identified on the basis of whole-probe CSD from during recovery sleep.
hippocampus = {
    "Segundo": LongCol[213:301],  # 4.25mm to 6.00mm from probe tip
    "Valentino": CheckPat[190:305],  # 3.8mm to 6.1mm from probe tip
    # "Doppio": CheckPat[190:291],  # 3.8mm to 5.8mm from probe tip, sleep
    "Doppio": CheckPat[190:301],  # 3.8mm to 6mm from probe tip, dex
    "Alessandro": LongCol[190:291],  # 3.8mm to 5.8mm from probe tip
    "Eugene": LongCol[240:311],  # 4.8mm to 6.2mm from probe tip
    "Allan": full["Allan"][175:291],  # 3.5mm to 5.8mm from probe tip
}

# Hippocampal channels, +/- additional channels above and below to allow for drift.
# This is probably unnecessary, even for Valentino.
drift_tracking = {
    "Segundo": LongCol[200:315],
    "Valentino": CheckPat[180:315],
    "Doppio": CheckPat[180:300],
    "Alessandro": LongCol[180:300],
    "Eugene": LongCol[230:320],
    "Allan": full["Allan"][170:300],
}

# Center of white matter should be ~400um from pyramidal layer, with lower and upper
# limits of ~266um and ~533um from the pyramidal layer, respectively.
white_matter = {
    "Segundo": [213],  # 380um from pyramidal inversion.
    "Valentino": [225],  # 400um from pyramidal inversion.
    "Doppio": [206],  # 400um from pyramidal inversion.
    "Alessandro": [205],  # 400um from pyramidal inversion.
    "Eugene": [243],  # 400um from pyramidal inversion.
    "Allan": [271],  # 400um from pyramidal inversion.
}

# All channels 140um to 200um ventral to the CA1 stratum pyramidale inversion.
# Based on a fixed offset relative to the stratum pyrmidale channels, identified
# during the first 2h of recvoery sleep. Used for power calculation, not SPW
# detection.
stratum_radiatum_140um_to_200um = {
    "Segundo": [155, 157, 159, 161],
    "Valentino": [165, 166, 169, 170],
    "Doppio": [146, 149, 150, 153],
    "Alessandro": [145, 147, 149, 151],
    "Eugene": [183, 185, 187, 189],
    "Allan": [211, 213, 215, 217],
}

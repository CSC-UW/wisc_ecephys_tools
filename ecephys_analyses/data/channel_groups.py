from ecephys.neuropixels import checkerboard_map, long_column_map

CheckPat = checkerboard_map.get_user_order()
LongCol = long_column_map.get_user_order()

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

# Visually identified in the LFP during the first 2h of recovery sleep
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
# Based on a fixed offset relative to the stratum pyrmidale channels, identified
# during the first 2h of recvoery sleep.
stratum_radiatum_140um_to_200um = {
    "Segundo": [155, 157, 159, 161],
    "Valentino": [165, 166, 169, 170],
    "Doppio": [146, 149, 150, 153],
    "Alessandro": [145, 147, 149, 151],
    "Eugene": [183, 185, 187, 189],
}

# Hippocampal channels, +/- additional channels above and below to allow for drift.
drift_tracking = {
    "Segundo": LongCol[200:315],
    "Valentino": CheckPat[180:315],
    "Doppio": CheckPat[180:300],
    "Alessandro": LongCol[180:300],
    "Eugene": LongCol[230:320],
}

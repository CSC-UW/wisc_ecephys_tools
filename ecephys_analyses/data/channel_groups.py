from ecephys.neuropixels import checkerboard_map, long_column_map

CheckPat = checkerboard_map.get_user_order()
LongCol = long_column_map.get_user_order()

full_names = {
    'Alessandro': 'CNPIX5-Alessandro',
    'Allan': 'CNPIX8-Allan',
    'Eugene': 'CNPIX6-Eugene',
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

# Depths intervals for each area, MUST CORRESPOND TO DEPTHS IN PHY!
depth_intervals = {
    "Alessandro": {
    5880:7660  
    },
    "Allan": {
        # 3-5-2021 imec0
        '3-5-2021_g0_imec0': { 'cortex': [5980, 7480], },
        '3-5-2021_g2_imec0': { 'cortex': [5980, 7480], },
        '3-5-2021_g3_imec0': { 'cortex': [5980, 7480], },
        '3-5-2021_g4_imec0': { 'cortex': [5980, 7480], },
        '3-5-2021_g5_imec0': { 'cortex': [5980, 7480], },
        '3-5-2021_g6_imec0': { 'cortex': [5980, 7480], },
        # 3-5-2021 imec1
        '3-5-2021_g0_imec1': { 'cortex': [7000, 8480], },
        '3-5-2021_g2_imec1': { 'cortex': [7000, 8480], },
        '3-5-2021_g3_imec1': { 'cortex': [7000, 8480], },
        '3-5-2021_g4_imec1': { 'cortex': [7000, 8480], },
        '3-5-2021_g5_imec1': { 'cortex': [7000, 8480], },
        '3-5-2021_g6_imec1': { 'cortex': [7000, 8480], },
    },
    "Eugene": {
        # imec 0
        '10-9-2020_NREM_depth1.5_imec0': { 'cortex': [6380, 7660] },
        '10-19-2020_NREM_depth1.5_imec0': { 'cortex': [6389, 7660] },
        '10-2-2020_NREM_depth1.4_imec0': { 'cortex': [6380, 7660] },
        '10-9-2020_NREM_depth1.2_imec0': { 'cortex': [6380, 7660] },
        '10-2-2020_NREM_depth1.1_imec0': { 'cortex': [6380, 7660] },
        '10-9-2020_NREM_depth0.9_imec0': { 'cortex': [6380, 7660] },
        '10-2-2020_NREM_depth0.8_imec0': { 'cortex': [6380, 7660] },
        '10-9-2020_NREM_depth0.6_imec0': { 'cortex': [6380, 7660] },
        '10-2-2020_NREM_depth0.5_imec0': { 'cortex': [6380, 7660] },
        '10-9-2020_NREM_depth0.3_imec0': { 'cortex': [6380, 7660] },
        '10-2-2020_NREM_depth0.2_imec0': { 'cortex': [6380, 7660] },
        '10-19-2020_REM_depth1.5_imec0': { 'cortex': [6380, 7660] },
        '10-2-2020_Wake_depth1.5_imec0': { 'cortex': [6380, 7660] },
        '10-9-2020_Wake_depth1.4_imec0': { 'cortex': [6380, 7660] },
        '10-2-2020_Wake_depth1.2_imec0': { 'cortex': [6380, 7660] },
        '10-9-2020_Wake_depth1.1_imec0': { 'cortex': [6380, 7660] },
        '10-2-2020_Wake_depth0.9_imec0': { 'cortex': [6380, 7660] },
        '10-9-2020_Wake_depth0.8_imec0': { 'cortex': [6380, 7660] },
        '10-2-2020_Wake_depth0.6_imec0': { 'cortex': [6380, 7660] },
        '10-9-2020_Wake_depth0.5_imec0': { 'cortex': [6380, 7660] },
        '10-2-2020_Wake_depth0.3_imec0': { 'cortex': [6380, 7660] },
        '10-9-2020_Wake_depth0.2_imec0': { 'cortex': [6380, 7660] },
        '10-2-2020_Sevo_depth1.5_imec0': { 'cortex': [6380, 7660] },
        '10-9-2020_Sevo_depth1.4_imec0': { 'cortex': [6380, 7660] },
        '10-2-2020_Sevo_depth1.2_imec0': { 'cortex': [6380, 7660] },
        '10-9-2020_Sevo_depth1.1_imec0': { 'cortex': [6380, 7660] },
        '10-2-2020_Sevo_depth0.9_imec0': { 'cortex': [6380, 7660] },
        '10-9-2020_Sevo_depth0.8_imec0': { 'cortex': [6380, 7660] },
        '10-2-2020_Sevo_depth0.6_imec0': { 'cortex': [6380, 7660] },
        '10-9-2020_Sevo_depth0.5_imec0': { 'cortex': [6380, 7660] },
        '10-2-2020_Sevo_depth0.3_imec0': { 'cortex': [6380, 7660] },
        '10-9-2020_Sevo_depth0.2_imec0': { 'cortex': [6380, 7660] },
        # imec 1
        '10-9-2020_NREM_depth1.5_imec1': { 'cortex': [5380, 7660] },
        '10-19-2020_NREM_depth1.5_imec1': { 'cortex': [5380, 7660] },
        '10-2-2020_NREM_depth1.4_imec1': { 'cortex': [5380, 7660] },
        '10-9-2020_NREM_depth1.2_imec1': { 'cortex': [5380, 7660] },
        '10-2-2020_NREM_depth1.1_imec1': { 'cortex': [5380, 7660] },
        '10-9-2020_NREM_depth0.9_imec1': { 'cortex': [5380, 7660] },
        '10-2-2020_NREM_depth0.8_imec1': { 'cortex': [5380, 7660] },
        '10-9-2020_NREM_depth0.6_imec1': { 'cortex': [5380, 7660] },
        '10-2-2020_NREM_depth0.5_imec1': { 'cortex': [5380, 7660] },
        '10-9-2020_NREM_depth0.3_imec1': { 'cortex': [5380, 7660] },
        '10-2-2020_NREM_depth0.2_imec1': { 'cortex': [5380, 7660] },
        '10-19-2020_REM_depth1.5_imec1': { 'cortex': [5380, 7660] },
        '10-2-2020_Wake_depth1.5_imec1': { 'cortex': [5380, 7660] },
        '10-9-2020_Wake_depth1.4_imec1': { 'cortex': [5380, 7660] },
        '10-2-2020_Wake_depth1.2_imec1': { 'cortex': [5380, 7660] },
        '10-9-2020_Wake_depth1.1_imec1': { 'cortex': [5380, 7660] },
        '10-2-2020_Wake_depth0.9_imec1': { 'cortex': [5380, 7660] },
        '10-9-2020_Wake_depth0.8_imec1': { 'cortex': [5380, 7660] },
        '10-2-2020_Wake_depth0.6_imec1': { 'cortex': [5380, 7660] },
        '10-9-2020_Wake_depth0.5_imec1': { 'cortex': [5380, 7660] },
        '10-2-2020_Wake_depth0.3_imec1': { 'cortex': [5380, 7660] },
        '10-9-2020_Wake_depth0.2_imec1': { 'cortex': [5380, 7660] },
        '10-2-2020_Sevo_depth1.5_imec1': { 'cortex': [5380, 7660] },
        '10-9-2020_Sevo_depth1.4_imec1': { 'cortex': [5380, 7660] },
        '10-2-2020_Sevo_depth1.2_imec1': { 'cortex': [5380, 7660] },
        '10-9-2020_Sevo_depth1.1_imec1': { 'cortex': [5380, 7660] },
        '10-2-2020_Sevo_depth0.9_imec1': { 'cortex': [5380, 7660] },
        '10-9-2020_Sevo_depth0.8_imec1': { 'cortex': [5380, 7660] },
        '10-2-2020_Sevo_depth0.6_imec1': { 'cortex': [5380, 7660] },
        '10-9-2020_Sevo_depth0.5_imec1': { 'cortex': [5380, 7660] },
        '10-2-2020_Sevo_depth0.3_imec1': { 'cortex': [5380, 7660] },
        '10-9-2020_Sevo_depth0.2_imec1': { 'cortex': [5380, 7660] },
    },
}

# stratum_radiatum = {"Doppio": CheckPat[260:273]}  # LF137 through LF161
# stratum_oriens_100um = {"Doppio": [177]}
# ripple_detection = {
#     "Segundo": [163, 165, 167, 169, 171, 173, 175, 177, 179, 181, 183],
#     "Valentino": [162, 165, 166, 169, 170, 173, 174, 177, 178, 181, 182],
#     "Doppio": [161, 162, 165, 166, 169, 170, 173, 174, 177, 178, 181],
#     "Alessandro": [159, 161, 163, 165, 167, 169, 171, 173, 175, 177, 179],
#     "Eugene": [193, 195, 197, 199, 201, 203, 205, 207, 209, 211],
# }

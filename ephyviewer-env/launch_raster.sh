#!/bin/bash
source ~/miniconda3/etc/profile.d/conda.sh 
conda activate ~/miniconda3/envs/ephyviewer
cd ~/projects/ephyviewer/wisc_ecephys_tools/ephyviewer-env
xterm -maximized -e python launch_raster.py

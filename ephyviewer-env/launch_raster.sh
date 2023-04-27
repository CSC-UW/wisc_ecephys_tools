#!/bin/bash
source /home/gfindlay/miniconda3/etc/profile.d/conda.sh 
conda activate /home/gfindlay/miniconda3/envs/ephyviewer
cd /home/gfindlay/projects/ephyviewer/wisc_ecephys_tools/ephyviewer-env
xterm -maximized -e python launch_raster.py

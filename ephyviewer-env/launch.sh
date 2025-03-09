#!/bin/bash
source ~/miniforge3/etc/profile.d/conda.sh 
conda activate ~/miniforge3/envs/ephyviewer
cd ~/projects/ephyviewer/wisc_ecephys_tools/ephyviewer-env
xterm -maximized -e python launch.py

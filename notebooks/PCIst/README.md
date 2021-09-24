# GENERATE PSTHs:

0. Activate the neuropixel environment: `conda activate /Volumes/scratch/neuropixels/miniconda3/envs/neuropix` 

1. Preprocess, sort and curate the data  

    1. Indicate the paths and outputs and regions for the datasets of interest

        1. Write the paths for each `condition` in `ecephys_analyses/data/datapaths.yml`

        2. Write the `condition_group` (set of conditions that we want to process) in `ecephys_analyses/data/roots.yml`

        2. Set the root directory where all data for the `condition_group` is saved, in `ecephys_analyses/data/roots.yml` . Wherever the parameter `root_key` is equal to `None`, the root used will be the `analysis_dir` key in `datapaths.yml`

        2. (optional) Set the regions of interest in `ecephys_analyses/data/regions.yml` 

        2. Make sure the full name of the subject is specified in `ecephys_analyses/data/channel_groups.py` 

    2. Copy, modify and run in order the following files to preprocess and sort the data. Make sure you set the right values for `condition_group` etc IN ALL THE FILES
        - `ecephys_analyses/notebooks/pipeline/run_catgt.ipynb`
        - `ecephys_analyses/notebooks/pipeline/run_sorting.ipynb`
        - `ecephys_analyses/notebooks/pipeline/run_kilosort_postprocessing.ipynb`

    3. Curate the data

    
2. For each condition, copy the `stim_times.yml` file in the condition directory (ie at `root_dir/subject_name/condition_name/stim_times.txt`)

    - The `stim_times.csv` files should have two columns: `sglx_stim_time` (in sec) and `stim_state` (eg "REM", "N2", "Wake")

    - NB: If you use a "combined" condition (ie a condition which concatenates multiple other conditions), make sure you concatenate the stim times as well!!



3. Copy, modify and run `ecephys_analyses/notebooks/PCIst/psth.ipynb`
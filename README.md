# ecephys_project_manager

## Installation
This will also install [`ecephys`](https://github.com/CSC-UW/ecephys) as a local, editable sibling directory.
```
git clone https://github.com/CSC-UW/ecephys.git
git clone https://github.com/CSC-UW/ecephys_project_manager.git

conda create -n myenv python=3
conda activate myenv

cd ecephys_project_manager
pip install -r requirements.txt
```

If you run into issues with h5py/hdf5 version compatibility within ipython/jupyter (but not python):
```
git clone https://github.com/CSC-UW/ecephys.git
git clone https://github.com/CSC-UW/ecephys_project_manager.git

conda create --name myenv python=3
conda activate myenv

conda install -c conda-forge --update-deps --force-reinstall hdf5 h5py

cd ecephys_project_manager
pip install -r requirements.txt
```

### Extra steps for spike sorting
So that spikeinterfacea can find your install locations:
```
export IRONCLUST_PATH='/Volumes/scratch/neuropixels/matlab/external/ironclust'
export KILOSORT_PATH='/Volumes/scratch/neuropixels/matlab/external/Kilosort-v1.0'
export KILOSORT2_PATH='/Volumes/scratch/neuropixels/matlab/external/Kilosort-v2.0'
export KILOSORT2_5_PATH='/Volumes/scratch/neuropixels/matlab/external/Kilosort-tb-v2.5'
export KILOSORT3_PATH='/Volumes/scratch/neuropixels/matlab/external/Kilosort-v3.0'
```
TODO: Set these paths as options in analysis_cfg.yaml, rather than as enviornment variables.

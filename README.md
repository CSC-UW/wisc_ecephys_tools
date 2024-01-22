# wisc_ecephys_tools

For extracellular electrophysiology code that is specific to the Wisconsin Institute for Sleep and Consciousness (WISC). This is code that depends on our particular data organization scheme, hardware, virtual environments, etc.

Generic code that might be immediately useful to people outside WISC should go in [`ecephys`](https://github.com/CSC-UW/ecephys).

## Installation
*Updated 1/22/2024 -- May be more recent than `CSC-UW/ece-env`.* 
[`ecephys`](https://github.com/CSC-UW/ecephys) is required. Read and satisfy those requirements, paying particular attention to the `ephyviewer` bit, if you intend to use that. 

If you run into issues with h5py/hdf5 version compatibility within ipython/jupyter (but not python):
```
git clone https://github.com/CSC-UW/ecephys.git
git clone https://github.com/CSC-UW/wisc_ecephys_tools.git

conda create --name myenv python=3
conda activate myenv

conda install -c conda-forge --update-deps --force-reinstall hdf5 h5py

cd wisc_ecephys_tools
pip install -r requirements.txt
```

### Spike sorting

Detailed instructions at `./script/sorting/README.md`

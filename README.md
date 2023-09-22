# wisc_ecephys_tools

For extracellular electrophysiology code that is specific to the Wisconsin Institute for Sleep and Consciousness (WISC). This is code that depends on our particular data organization scheme, hardware, virtual environments, etc.

Generic code that might be immediately useful to people outside WISC should go in [`ecephys`](https://github.com/CSC-UW/ecephys).

## Installation
This will also install [`ecephys`](https://github.com/CSC-UW/ecephys) as a local, editable sibling directory.
```
git clone https://github.com/CSC-UW/ecephys.git
git clone https://github.com/CSC-UW/wisc_ecephys_tools.git

conda create -n myenv python=3
conda activate myenv

cd ecephys
pip install -e .

cd ..
cd wisc_ecephys_tools
pip install -e .
```

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

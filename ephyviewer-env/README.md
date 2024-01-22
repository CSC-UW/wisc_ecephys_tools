On e.g. `tononi-2`:

1. Install mambaforge
```
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh"
bash Mambaforge-$(uname)-$(uname -m).sh
```
2. Clone all the repositories you will need:
```
# Instead of doing this, why don't we at least install spikeinterface and ephyviewer directly from github, non-editable? 
mkdir ~/projects/ephyviewer/
cd ~/projects/ephyviewer/
git clone https://github.com/CSC-UW/ephyviewer.git
git clone https://github.com/CSC-UW/ecephys.git
git clone https://github.com/CSC-UW/wisc_ecephys_tools.git
git clone https://github.com/CSC-UW/spikeinterface.git
```
3. Use the `wisc/dev` branch of `CSC-UW/spikeinterface`:
```
cd spikeinterface
git checkout wisc/dev
cd ..
```
4. Install
```
mamba create -n ephyviewer python=3.11
mamba activate ephyviewer
pip install pyside6
pip install -e ./spikeinterface
pip install -e ./ephyviewer
pip install -e ./ecephys
pip install -e ./wisc_ecephys_tools
```
5. Move `launch_raster.sh` to desktop, add +x, and edit paths if necessary. 

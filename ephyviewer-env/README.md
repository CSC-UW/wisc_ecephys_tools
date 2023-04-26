On e.g. `tononi-2`:

1. Install mambaforge
```
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh"
bash Mambaforge-$(uname)-$(uname -m).sh
```
2. Install poetry version 1.3.1 (to avoid keyring issues with latest version)
```
curl -sSL https://install.python-poetry.org | python3 - --version 1.3.1
```
3. Clone all the repositories you will need:
```
mkdir ~/projects/ephyviewer/
cd ~/projects/ephyviewer/
git clone https://github.com/CSC-UW/ecephys.git
git clone https://github.com/CSC-UW/wisc_ecephys_tools.git
git clone https://github.com/CSC-UW/spikeinterface.git
```
4. Install
```
mamba create -n ephyviewer python=3.10 pyqt
mamba activate ephyviewer
cd ~/projects/ephyviewer/wisc_ecephys_tools/ephyviewer-env
pip install sortednp # Wheel building is broken WITHIN sortednp. Poetry will fail.
poetry install
```
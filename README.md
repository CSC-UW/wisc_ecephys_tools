# ecephys_analyses

## Installation
This will also install `ecephys` as a local, editable sibling directory.
```
git clone https://github.com/CSC-UW/ecephys.git
git clone https://github.com/grahamfindlay/ecephys_analyses.git

conda create -n myenv python=3
conda activate myenv

cd ecephys_analyses
pip install -r requirements.txt
```
Because `jupyter` is installed as a dependency of `ecephys_analyses`, you do not have to do anything else in order to edit all included notebooks in VSCode.
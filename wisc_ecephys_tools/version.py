from os.path import join as pjoin

# Format expected by setup.py and doc/source/conf.py: string of form "X.Y.Z"
_version_major = 0
_version_minor = 1
_version_micro = ""  # use '' for first of series, number for 1 and above
_version_extra = "dev"
# _version_extra = ''  # Uncomment this for full releases

# Construct full version string from these.
_ver = [_version_major, _version_minor]
if _version_micro:
    _ver.append(_version_micro)
if _version_extra:
    _ver.append(_version_extra)

__version__ = ".".join(map(str, _ver))

CLASSIFIERS = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Intended Audience :: Science/Research",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Scientific/Engineering",
]

# Description should be a one-liner:
description = "wisc_ecephys_tools"
# Long description will go up on the pypi page
long_description = """
Tools for managing (e)xtra(c)ellular (e)lectro(phys)iology projects
at the Wisconsin Institute for Sleep and Consciousness.
"""

NAME = "wisc_ecephys_tools"
MAINTAINER = "Graham Findlay"
MAINTAINER_EMAIL = "gfindlay@wisc.edu"
DESCRIPTION = description
LONG_DESCRIPTION = long_description
URL = "http://github.com/CSC-UW/wisc_ecephys_tools"
DOWNLOAD_URL = ""
LICENSE = ""
AUTHOR = "Graham Findlay"
AUTHOR_EMAIL = "gfindlay@wisc.edu"
PLATFORMS = "OS Independent"
MAJOR = _version_major
MINOR = _version_minor
MICRO = _version_micro
VERSION = __version__
PACKAGE_DATA = {"wisc_ecephys_tools": [pjoin("static", "*")]}
EXTRAS_REQUIRE = {}
INSTALL_REQUIRES = [
    "numpy",
    "pyyaml",
    "black",
    "ecephys",
    "sglxarray",
    "spikeinterface",  # @ git+https://github.com/CSC-UW/spikeinterface.git@master#egg=spikeinterface"
    "ecephys_spike_sorting",  # @ git+https://github.com/CSC-UW/ecephys_spike_sorting.git@master#egg=ecephys_spike_sorting"
]
PYTHON_REQUIRES = ">= 3.10"

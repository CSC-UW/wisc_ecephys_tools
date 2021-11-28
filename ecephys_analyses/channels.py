import numpy as np

from .package_data import package_datapath
from .utils import load_yaml_doc


def get_channels(subject, experiment, probe, group, asarray=True):
    doc = load_yaml_doc(package_datapath("channels.yaml"))
    chans = doc[subject][experiment][probe][group]
    return np.asarray(chans) if asarray else chans

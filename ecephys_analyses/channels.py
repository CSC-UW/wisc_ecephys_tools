import numpy as np

from .package_data import package_datapath
from .utils import load_yaml_stream, get_subject_document


def get_channels(subject, experiment, probe, group, asarray=True):
    stream = load_yaml_stream(package_datapath("channels.yaml"))
    doc = get_subject_document(stream, subject)
    chans = doc["experiments"][experiment]["probes"][probe][group]
    return np.asarray(chans) if asarray else chans

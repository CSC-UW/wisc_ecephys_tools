import numpy as np

from .conf import get_config_file
from .utils import load_yaml_stream, get_subject_document


def get_channels(subject, experiment, probe, group, asarray=True):
    stream = load_yaml_stream(get_config_file("channels.yaml"))
    doc = get_subject_document(stream, subject)
    chans = doc["experiments"][experiment]["probes"][probe][group]
    return np.asarray(chans) if asarray else chans

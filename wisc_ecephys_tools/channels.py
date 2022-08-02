import numpy as np

from .conf import get_config_file, get_subject_file
from .utils import load_yaml_stream, get_subject_document, load_yaml_doc
# TODO: This module is ready for file-per-subject


def get_channels(subject, experiment, probe, group, asarray=True):
    try:
        doc = load_yaml_doc(get_subject_file(subject))
    except:
        stream = load_yaml_stream(get_config_file("channels.yaml"))
        doc = get_subject_document(stream, subject)
    chans = doc["experiments"][experiment]["probes"][probe][group]
    return np.asarray(chans) if asarray else chans

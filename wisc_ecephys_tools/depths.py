from .conf import get_config_file, get_subject_file
from .utils import load_yaml_stream, get_subject_document, load_yaml_doc

# TODO: This module is ready for file-per-subject


def get_depths(subject, experiment, probe, region):
    try:
        doc = load_yaml_doc(get_subject_file(subject))
    except:
        stream = load_yaml_stream(get_config_file("depths.yaml"))
        doc = get_subject_document(stream, subject)
    return doc["experiments"][experiment]["probes"][probe][region]


def get_regions(subject, experiment, probe):
    try:
        doc = load_yaml_doc(get_subject_file(subject))
    except:
        stream = load_yaml_stream(get_config_file("depths.yaml"))
        doc = get_subject_document(stream, subject)
    return doc["experiments"][experiment]["probes"][probe]

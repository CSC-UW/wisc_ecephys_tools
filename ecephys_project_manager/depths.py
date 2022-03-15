from .conf import get_config_file
from .utils import load_yaml_stream, get_subject_document


def get_depths(subject, experiment, probe, region):
    stream = load_yaml_stream(get_config_file("depths.yaml"))
    doc = get_subject_document(stream, subject)
    return doc["experiments"][experiment]["probes"][probe][region]


def get_regions(subject, experiment, probe):
    stream = load_yaml_stream(get_config_file("depths.yaml"))
    doc = get_subject_document(stream, subject)
    return doc["experiments"][experiment]["probes"][probe]

from .conf import get_config_file
from .utils import load_yaml_stream, get_subject_document


def get_region_depths(subject, experiment, alias, probe):
    """Return {<region>: <region_depths>} dict for a probe/alias."""
    stream = load_yaml_stream(get_config_file("regions.yaml"))
    doc = get_subject_document(stream, subject)
    return doc["experiments"][experiment]["aliases"][alias]["probes"][probe]
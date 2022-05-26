from .conf import get_config_file
from .utils import load_yaml_stream, get_subject_document


def get_cluster_group_dict(subject, experiment, alias, probe):
    """Return {<cluster_group_label>: <cluster_list>} dict for a probe/alias."""
    stream = load_yaml_stream(get_config_file("cluster_groups.yaml"))
    doc = get_subject_document(stream, subject)
    return doc["experiments"][experiment]["aliases"][alias]["probes"][probe]
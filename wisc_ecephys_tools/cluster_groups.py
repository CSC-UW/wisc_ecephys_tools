from .conf import get_config_file, get_subject_file
from .utils import load_yaml_stream, get_subject_document, load_yaml_doc

# TODO: This module is ready for file-per-subject
# TODO: Remove this module, as cluster_groups.yaml is unused.


def get_cluster_group_dict(subject, experiment, alias, probe):
    """Return {<cluster_group_label>: <cluster_list>} dict for a probe/alias."""
    try:
        doc = load_yaml_doc(get_subject_file(subject))
    except:
        stream = load_yaml_stream(get_config_file("cluster_groups.yaml"))
        doc = get_subject_document(stream, subject)
    return doc["experiments"][experiment]["aliases"][alias]["probes"][probe]

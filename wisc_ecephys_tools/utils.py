import yaml

# TODO: This module is ready for file-per-subject


def load_yaml_doc(yaml_path):
    """Load a YAML file that contains only one document."""
    with open(yaml_path) as fp:
        yaml_doc = yaml.safe_load(fp)
    return yaml_doc


# TODO: This function should no longer be necessary after conversion to file-per-subject
def load_yaml_stream(yaml_path):
    """Load all YAML documents in a file."""
    with open(yaml_path) as fp:
        yaml_stream = list(yaml.safe_load_all(fp))
    return yaml_stream


# TODO: This function should no longer be necessary after conversion to file-per-subject
def get_subject_document(yaml_stream, subject_name):
    """Get a subject's YAML document from a YAML stream.

    YAML documents must contain a 'subject' field:
    ---
    subject: subject_name
    ...
    """
    matches = [doc for doc in yaml_stream if doc["subject"] == subject_name]
    assert len(matches) == 1, f"Exactly 1 YAML document should match {subject_name}"
    return matches[0]

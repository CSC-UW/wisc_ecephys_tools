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

"""Access params specified in data/analysis_cfg.yaml"""

from pathlib import Path

import yaml

from .paths import package_datapath

YAML_FILENAME = "analysis_cfg.yaml"


def load_yaml():
    yaml_path = Path(package_datapath(YAML_FILENAME))
    if not yaml_path.exists():
        raise FileNotFoundError(
            f'Could not find file at {yaml_path}'
        )
    with open(yaml_path) as fp:
        yaml_stream = list(yaml.safe_load_all(fp))
    # validate like a boss
    assert all('analysis_type' in s for s in yaml_stream)
    assert all('analysis_params' in s for s in yaml_stream)
    analysis_types = [
        doc['analysis_type'] for doc in yaml_stream
    ]
    if not len(yaml_stream) == len(set(analysis_types)):
        raise ValueError(
            f"Found more than 1 document per analysis type in `{YAML_FILENAME}`"
        )
    return yaml_stream


def get_analysis_doc(analysis_type):
    yaml_stream = load_yaml()
    analysis_types = [
        doc['analysis_type'] for doc in yaml_stream
    ]
    if not analysis_type in analysis_types:
        raise ValueError(
            f"No document for analysis type `{analysis_type}` in "
            f"{YAML_FILENAME} file"
        )
    return next(doc for doc in yaml_stream if doc['analysis_type'] == analysis_type)


def get_analysis_params(analysis_type, analysis_name):
    analysis_doc = get_analysis_doc(analysis_type)
    if not analysis_name in analysis_doc['analysis_params']:
        raise ValueError(
            f"Could not find `{analysis_name}` key in the following analysis doc loaded from {YAML_FILENAME}: {analysis_doc}"
        )
    return analysis_doc['analysis_params'][analysis_name]
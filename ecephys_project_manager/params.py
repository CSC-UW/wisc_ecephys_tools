"""Access params specified in data/analysis_cfg.yaml"""

from pathlib import Path

import yaml

from .conf import get_config_file

YAML_FILENAME = "analysis_cfg.yaml"


def load_yaml(config_dir=None):
    yaml_path = Path(get_config_file(YAML_FILENAME, config_dir=config_dir))
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


def get_analysis_doc(analysis_type, config_dir=None):
    yaml_stream = load_yaml(config_dir=config_dir)
    analysis_types = [
        doc['analysis_type'] for doc in yaml_stream
    ]
    if not analysis_type in analysis_types:
        raise ValueError(
            f"No document for analysis type `{analysis_type}` in "
            f"{YAML_FILENAME} file"
        )
    return next(doc for doc in yaml_stream if doc['analysis_type'] == analysis_type)


def get_analysis_params(analysis_type, analysis_name, config_dir=None):
    analysis_doc = get_analysis_doc(analysis_type, config_dir=config_dir)
    if not analysis_name in analysis_doc['analysis_params']:
        raise ValueError(
            f"Could not find `{analysis_name}` key in the following analysis doc loaded from {YAML_FILENAME}: {analysis_doc}"
        )
    return analysis_doc['analysis_params'][analysis_name]

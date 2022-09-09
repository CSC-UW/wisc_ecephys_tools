"""Access params specified in params.yaml"""
import os
import yaml
from pathlib import Path

DEFAULT_PARAMS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def get_params_file(params_dir=DEFAULT_PARAMS_DIRECTORY, filename="params.yaml"):
    return Path(os.path.join(params_dir, filename))


def load_yaml(params_dir=DEFAULT_PARAMS_DIRECTORY):
    yaml_path = get_params_file(params_dir=params_dir)
    if not yaml_path.exists():
        raise FileNotFoundError(f"Could not find file at {yaml_path}")
    with open(yaml_path) as fp:
        yaml_stream = list(yaml.safe_load_all(fp))
    # validate like a boss
    assert all("analysis_type" in s for s in yaml_stream)
    assert all("analysis_params" in s for s in yaml_stream)
    analysis_types = [doc["analysis_type"] for doc in yaml_stream]
    if not len(yaml_stream) == len(set(analysis_types)):
        raise ValueError(
            f"Found more than 1 document per analysis type in `{yaml_path}`"
        )
    return yaml_stream


def get_analysis_doc(analysis_type, params_dir=DEFAULT_PARAMS_DIRECTORY):
    yaml_stream = load_yaml(params_dir)
    analysis_types = [doc["analysis_type"] for doc in yaml_stream]
    if not analysis_type in analysis_types:
        raise ValueError(
            f"No document for analysis type `{analysis_type}` in {params_dir}"
        )
    return next(doc for doc in yaml_stream if doc["analysis_type"] == analysis_type)


def get_analysis_params(
    analysis_type, parameter_group, params_dir=DEFAULT_PARAMS_DIRECTORY
):
    analysis_doc = get_analysis_doc(analysis_type, params_dir)
    if not parameter_group in analysis_doc["analysis_params"]:
        raise ValueError(
            f"Could not find `{parameter_group}` key in the following analysis doc loaded from: {analysis_doc}"
        )
    return analysis_doc["analysis_params"][parameter_group]

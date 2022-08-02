import os
import yaml

PACKAGE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIRECTORY = os.path.join(PACKAGE_DIRECTORY, "config")


def get_config_file(filename, config_dir=None):
    if config_dir is None:
        config_dir = CONFIG_DIRECTORY
    return os.path.join(config_dir, filename)


def load_yaml_doc(yaml_path):
    """Load a YAML file that contains only one document."""
    with open(yaml_path) as fp:
        yaml_doc = yaml.safe_load(fp)
    return yaml_doc


def load_yaml_stream(yaml_path):
    """Load all YAML documents in a file."""
    with open(yaml_path) as fp:
        yaml_stream = list(yaml.safe_load_all(fp))
    return yaml_stream

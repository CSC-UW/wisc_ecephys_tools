import os

PACKAGE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIRECTORY = os.path.join(PACKAGE_DIRECTORY, "config")


def get_config_file(filename, config_dir=None):
    if config_dir is None:
        config_dir = CONFIG_DIRECTORY
    return os.path.join(config_dir, filename)

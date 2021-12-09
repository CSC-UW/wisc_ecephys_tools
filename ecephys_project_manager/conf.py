import os

PACKAGE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIRECTORY = os.path.join(PACKAGE_DIRECTORY, "config")


def get_config_file(filename):
    return os.path.join(CONFIG_DIRECTORY, filename)

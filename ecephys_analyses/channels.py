import os
import yaml
import numpy as np

MODULE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
YAML_PATH = os.path.join(MODULE_DIRECTORY, "channels.yaml")


def get_channels(subject, experiment, probe, group):
    with open(YAML_PATH) as fp:
        yaml_data = yaml.safe_load(fp)

    return np.asarray(yaml_data[subject][experiment][probe][group])
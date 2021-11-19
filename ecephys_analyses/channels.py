import yaml
import numpy as np
from .paths import package_datapath


def get_channels(subject, experiment, probe, group, asarray=True):
    yaml_path = package_datapath("channels.yaml")
    with open(yaml_path) as fp:
        yaml_data = yaml.safe_load(fp)

    chans = yaml_data[subject][experiment][probe][group]
    return np.asarray(chans) if asarray else chans

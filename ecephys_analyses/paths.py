from .package_data import package_datapath
from .utils import load_yaml_stream
from .sglx.experiments import get_files


##### RAW DATA PATH FUNCTIONS #####
def get_sglx_files(subject, experiment, alias=None, **kwargs):
    sessions_stream = load_yaml_stream(package_datapath("sglx_sessions.yaml"))
    experiments_stream = load_yaml_stream(package_datapath("sglx_experiments.yaml"))
    return get_files(
        sessions_stream, experiments_stream, subject, experiment, alias, **kwargs
    )


def get_lfp_bin_paths(subject, experiment, alias=None, **kwargs):
    return (
        get_sglx_files(subject, experiment, alias, stream="lf", ftype="bin", **kwargs)
        .sort_values("fileCreateTime", ascending=True)
        .path.values
    )

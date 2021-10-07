import os
from ecephys.data_mgmt import paths
import yaml
from ecephys.sglx.session_org_utils import get_files, _get_session_style_path_parts
from ecephys.sglx.file_mgmt import parse_sglx_fname
from pathlib import Path

MODULE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
YAML_PATH = os.path.join(MODULE_DIRECTORY, "paths.yaml")

PACKAGE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DATA_DIRECTORY = os.path.join(PACKAGE_DIRECTORY, "data")


def package_datapath(filename):
    return os.path.join(PACKAGE_DATA_DIRECTORY, filename)


##### RAW DATA PATH FUNCTIONS #####

# TODO: Retire this function
def get_sglx_style_datapaths(subject, experiment, condition, ext):
    return paths.get_sglx_style_datapaths(
        YAML_PATH, subject, experiment, condition, ext
    )


def get_raw_files(subject, experiment, alias=None, **kwargs):
    yaml_path = package_datapath("sessions.yaml")
    with open(yaml_path) as fp:
        yaml_stream = list(yaml.safe_load_all(fp))
    return get_files(yaml_stream, subject, experiment, alias, **kwargs)


def get_lfp_bin_paths(subject, experiment, alias=None, **kwargs):
    return (
        get_raw_files(subject, experiment, alias, stream="lf", ftype="bin", **kwargs)
        .sort_values("fileCreateTime", ascending=True)
        .path.values
    )


##### ANALYSIS PATH FUNCTIONS #####
# These functions all assume the same analysis, i.e. 1 yaml doc

# TODO: Retire this function
def get_datapath(file, subject, experiment, condition=None):
    return paths.get_datapath(YAML_PATH, file, subject, experiment, condition)


def get_analysis_yaml_doc():
    yaml_path = package_datapath("analysis_paths.yaml")
    with open(yaml_path) as fp:
        yaml_doc = yaml.safe_load(fp)
    return yaml_doc


def get_subject_dirname(subject):
    doc = get_analysis_yaml_doc()
    return doc["subject_directories"][subject]


def _get_project_dir():
    doc = get_analysis_yaml_doc()
    return Path(doc["project_directory"])


def get_project_dir(subject=None):
    subject_dirname = get_subject_dirname(subject) if subject else ""
    return _get_project_dir() / subject_dirname


def get_experiment_dir(experiment, subject=None):
    subject_dirname = get_subject_dirname(subject) if subject else ""
    return get_project_dir() / experiment / subject_dirname


def get_alias_dir(experiment, alias, subject=None):
    subject_dirname = get_subject_dirname(subject) if subject else ""
    return get_experiment_dir(experiment) / alias / subject_dirname


def get_project_file(fname, subject=None):
    return get_project_dir(subject) / fname


def get_experiment_file(fname, experiment, subject=None):
    return get_experiment_dir(experiment, subject) / fname


def get_alias_file(fname, experiment, alias, subject=None):
    return get_alias_dir(experiment, alias, subject) / fname


def _get_analysis_counterpart(path, extension, analysis_subject_dir):
    (
        subject_dir,
        session_dirname,
        session_sglx_dirname,
        gate_dirname,
        probe_dirname,
        fname,
    ) = _get_session_style_path_parts(path)
    (run, gate, trigger, probe, stream, ftype) = parse_sglx_fname(fname)
    new_fname = f"{run}_{gate}_{trigger}.{probe}.{extension}"
    return (
        analysis_subject_dir
        / session_dirname
        / session_sglx_dirname
        / gate_dirname
        / probe_dirname
        / new_fname
    )


def _get_analysis_counterparts(paths, extension, analysis_subject_dir):
    counterparts = [
        _get_analysis_counterpart(p, extension, analysis_subject_dir) for p in paths
    ]
    return list(dict.fromkeys(counterparts))


def get_analysis_counterparts(paths, extension, subject):
    return _get_analysis_counterparts(paths, extension, get_project_dir(subject))

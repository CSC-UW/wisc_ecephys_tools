"""
Experiments + aliases assumed, sessions not?
Only projects.yaml is required to resolve paths?

- project_dir/ (e.g. SPWRs/)
  - subject_dir/ (e.g. ANPIX11-Adrian/)
  - experiment_dir/ (e.g. novel_objects_deprivation/)
    - alias_dir/ (e.g. recovery_sleep/)
      - alias_subject_dir/ (e.g. ANPIX11-Adrian/)
    - subalias_dir/ (e.g. sleep_homeostasis_0/, sleep_homeostasis_1/) <- Only if there is N>1 subaliases
      - subalias_subject_dir/ (e.g. ANPIX11-Adrian/)
    - experiment_subject_dir/ (e.g. ANPIX11-Adrian/)

"""
from pathlib import Path
from ecephys.sglx.file_mgmt import parse_sglx_fname

from .package_data import package_datapath
from .utils import load_yaml_stream, remove_duplicates
from .sglx_sessions import get_filepath_relative_to_session_directory_parent
from .experiments_and_aliases import SUBALIAS_IDX_DF_VALUE

# You could name a project the same thing as an experiment
# You could name a project "Common" or "Scoring" or "Sorting"


def get_project_document(yaml_stream, project_name):
    """Get a project's YAML document from a YAML stream.

    YAML documents must contain a 'project' field:
    ---
    project: project_name
    ...
    """
    matches = [doc for doc in yaml_stream if doc["project"] == project_name]
    assert len(matches) == 1, f"Exactly 1 YAML document should match {project_name}"
    return matches[0]


def get_subalias_dirname(alias_name, subalias_idx=None):
    if subalias_idx is None or subalias_idx == SUBALIAS_IDX_DF_VALUE:
        return alias_name
    return f"{alias_name}_{subalias_idx}"

##### Functions for getting directories


def get_project_directory(project_name):
    """Get a project directory described in projects.yaml"""
    stream = load_yaml_stream(package_datapath("projects.yaml"))
    doc = get_project_document(stream, project_name)
    return Path(doc["project_directory"])


def get_subject_directory(project_name, subject_name):
    """Get a subject's directory for this project."""
    return get_project_directory(project_name) / subject_name


def get_experiment_directory(project_name, experiment_name):
    return get_project_directory(project_name) / experiment_name


def get_alias_directory(project_name, experiment_name, alias_name, subalias_idx=None):
    return get_experiment_directory(project_name, experiment_name) / get_subalias_dirname(alias_name, subalias_idx)


def get_experiment_subject_directory(project_name, experiment_name, subject_name):
    return get_experiment_directory(project_name, experiment_name) / subject_name


def get_alias_subject_directory(
    project_name, experiment_name, alias_name, subject_name
):
    return get_alias_directory(project_name, experiment_name, alias_name) / subject_name


def get_alias_subject_directory(
    project_name, experiment_name, alias_name, subject_name, subalias_idx=None
):
    return get_alias_directory(project_name, experiment_name, alias_name, subalias_idx=subalias_idx) / subject_name


##### Functions for getting files


def get_project_file(project_name, fname):
    return get_project_directory(project_name) / fname


def get_subject_file(project_name, subject_name, fname):
    return get_subject_directory(project_name, subject_name) / fname


def get_experiment_file(project_name, experiment_name, fname):
    return get_experiment_directory(project_name, experiment_name) / fname


def get_alias_file(project_name, experiment_name, alias_name, fname, subalias_idx=None):
    return get_alias_directory(project_name, experiment_name, alias_name, subalias_idx=subalias_idx) / fname


def get_experiment_subject_file(project_name, experiment_name, subject_name, fname):
    return (
        get_experiment_subject_directory(project_name, experiment_name, subject_name)
        / fname
    )


def get_alias_subject_file(
    project_name, experiment_name, alias_name, subject_name, fname
):
    return (
        get_alias_subject_directory(
            project_name, experiment_name, alias_name, subject_name
        )
        / fname
    )


##### Functions for mirroring


def mirror_raw_data_path(mirror_parent, path):
    return mirror_parent / get_filepath_relative_to_session_directory_parent(path)


def mirror_raw_data_paths(mirror_parent, paths):
    return [mirror_raw_data_path(mirror_parent, p) for p in paths]


def mirror_raw_data_paths_at_subject_directory(project_name, subject_name, paths):
    mirror_parent = get_subject_directory(project_name, subject_name)
    return mirror_raw_data_paths(mirror_parent, paths)


##### Functions for getting project counterparts


def get_project_counterparts(project_name, subject_name, paths, extension):
    mirrors = mirror_raw_data_paths_at_subject_directory(
        project_name, subject_name, paths
    )
    counterparts = [p.with_suffix(extension) for p in mirrors]
    return remove_duplicates(counterparts)

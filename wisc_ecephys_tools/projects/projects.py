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
import os
import yaml
from pathlib import Path

# You could name a project the same thing as an experiment
# You could name a project "Common" or "Scoring" or "Sorting"

DEFAULT_PROJECTS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def get_projects_file(
    filename="projects.yaml", projects_dir=DEFAULT_PROJECTS_DIRECTORY
):
    return Path(os.path.join(projects_dir, filename))


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def load_yaml_stream(yaml_path):
    """Load all YAML documents in a file."""
    with open(yaml_path) as fp:
        yaml_stream = list(yaml.safe_load_all(fp))
    return yaml_stream


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
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


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_subalias_dirname(alias_name, subalias_idx=None):
    if (subalias_idx is None) or (subalias_idx == -1):
        return alias_name
    return f"{alias_name}_{subalias_idx}"


##### Functions for getting directories


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_project_directory(project_name):
    """Get a project directory described in projects.yaml"""
    stream = load_yaml_stream(get_projects_file())
    doc = get_project_document(stream, project_name)
    return Path(doc["project_directory"])


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_subject_directory(project_name, subject_name):
    """Get a subject's directory for this project."""
    return get_project_directory(project_name) / subject_name


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_experiment_directory(project_name, experiment_name):
    return get_project_directory(project_name) / experiment_name


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_alias_directory(project_name, experiment_name, alias_name, subalias_idx=None):
    return get_experiment_directory(
        project_name, experiment_name
    ) / get_subalias_dirname(alias_name, subalias_idx)


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_experiment_subject_directory(project_name, experiment_name, subject_name):
    return get_experiment_directory(project_name, experiment_name) / subject_name


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_alias_subject_directory(
    project_name, experiment_name, alias_name, subject_name
):
    return get_alias_directory(project_name, experiment_name, alias_name) / subject_name


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_alias_subject_directory(
    project_name, experiment_name, alias_name, subject_name, subalias_idx=None
):
    return (
        get_alias_directory(
            project_name, experiment_name, alias_name, subalias_idx=subalias_idx
        )
        / subject_name
    )


##### Functions for getting files


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_project_file(project_name, fname):
    return get_project_directory(project_name) / fname


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_project_subject_file(project_name, subject_name, fname):
    return get_subject_directory(project_name, subject_name) / fname


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_experiment_file(project_name, experiment_name, fname):
    return get_experiment_directory(project_name, experiment_name) / fname


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_alias_file(project_name, experiment_name, alias_name, fname, subalias_idx=None):
    return (
        get_alias_directory(
            project_name, experiment_name, alias_name, subalias_idx=subalias_idx
        )
        / fname
    )


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_experiment_subject_file(project_name, experiment_name, subject_name, fname):
    return (
        get_experiment_subject_directory(project_name, experiment_name, subject_name)
        / fname
    )


# TODO: Deprecated, will be removed. Use ecephys.wne instead.
def get_alias_subject_file(
    project_name, experiment_name, alias_name, subject_name, fname
):
    return (
        get_alias_subject_directory(
            project_name, experiment_name, alias_name, subject_name
        )
        / fname
    )

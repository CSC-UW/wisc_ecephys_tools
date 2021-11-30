"""
Experiments + aliases assumed, sessions not?
Only projects.yaml is required to resolve paths?

- project_dir/ (e.g. SPWRs/)
  - subject_dir/ (e.g. ANPIX11-Adrian/)
  - experiment_dir/ (e.g. novel_objects_deprivation/)
    - alias_dir/ (e.g. recovery_sleep/)
      - alias_subject_dir/ (e.g. ANPIX11-Adrian/)
    - experiment_subject_dir/ (e.g. ANPIX11-Adrian/)

"""
from pathlib import Path
from ecephys.sglx.file_mgmt import parse_sglx_fname

from .package_data import package_datapath
from .utils import load_yaml_stream, remove_duplicates
from .sglx_sessions import get_filepath_relative_to_session_directory_parent

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


def get_alias_directory(project_name, experiment_name, alias_name):
    return get_experiment_directory(project_name, experiment_name) / alias_name


def get_experiment_subject_directory(project_name, experiment_name, subject_name):
    return get_experiment_directory(project_name, experiment_name) / subject_name


def get_alias_subject_directory(
    project_name, experiment_name, alias_name, subject_name
):
    return get_alias_directory(project_name, experiment_name, alias_name) / subject_name


##### Functions for getting files


def get_project_file(project_name, fname):
    return get_project_directory(project_name) / fname


def get_subject_file(project_name, subject_name, fname):
    return get_subject_directory(project_name, subject_name) / fname


def get_experiment_file(project_name, experiment_name, fname):
    return get_experiment_directory(project_name, experiment_name) / fname


def get_alias_file(project_name, experiment_name, alias_name, fname):
    return get_alias_directory(project_name, experiment_name, alias_name) / fname


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


##### Functions for getting project counterparts


def replace_ftype(path, extension, remove_probe=False, remove_stream=False):
    """Replace a SpikeGLX filetype extension (i.e. .bin or .meta), and optionally strip
    the probe and/or stream suffixes (e.g. .imec0 and .lf) while doing so.

    Parameters:
    -----------
    path: pathlib.Path
    extension: str
        The desired final suffix(es), e.g. '.emg.nc' or '.txt'
    remove_probe: bool (default: False)
        If true, strip the probe suffix.
    remove_stream: bool (default=False)
        If True, strip the stream suffix.
    """
    run, gate, trigger, probe, stream, ftype = parse_sglx_fname(path.name)

    name = path.with_suffix(extension).name
    name = name.replace(f".{probe}", "") if remove_probe else name
    name = name.replace(f".{stream}", "") if remove_stream else name

    return path.with_name(name)


def get_project_counterparts(
    project_name,
    subject_name,
    paths,
    extension,
    remove_probe=False,
    remove_stream=False,
):
    """Get counterparts to SpikeGLX raw data files.

    Counterparts are mirrored at the project's subject directory, and likely
    have different suffixes than the original raw data files.

    Parameters:
    -----------
    project_name: str
        From projects.yaml
    subject_name: str
        Subject's name within this project, i.e. subject's directory name.
    paths: list of pathlib.Path
        The raw data files to get the counterparts of.
    extension:
        The extension to replace .bin or .meta with. See `replace_ftype`.

    Returns:
    --------
    list of pathlib.Path
    """
    counterparts = mirror_raw_data_paths(
        get_subject_directory(project_name, subject_name), paths
    )  # Mirror paths at the project's subject directory
    counterparts = [
        replace_ftype(p, extension, remove_probe, remove_stream) for p in counterparts
    ]
    return remove_duplicates(counterparts)

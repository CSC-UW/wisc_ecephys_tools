from ecephys.sglx.file_mgmt import parse_sglx_fname
from .sessions import get_filepath_relative_to_session_directory_parent
from ..projects import get_subject_directory
from ..utils import remove_duplicates

##### Functions for mirroring


def mirror_raw_data_path(mirror_parent, path):
    """Mirror a path to raw SpikeGLX data, maintaining session-style data/directory organization, but at a new path root.
    For example...
    `/foo/bar/1-1-2021/SpikeGLX/1-1-2021_g0/1-1-2021_g0_imec0/1-1-2021_g0_t0.imec0.lf.bin`
    ...might become...
    `/baz/qux/1-1-2021/SpikeGLX/1-1-2021_g0/1-1-2021_g0_imec0/1-1-2021_g0_t0.imec0.lf.bin`

    Parameters:
    -----------
    mirror_parent: pathlib.Path
        The new root to mirror at, e.g. `/baz/qux`
    path: pathlib.Path
        The old filepath, e.g. `/foo/bar/1-1-2021/SpikeGLX/1-1-2021_g0/1-1-2021_g0_imec0/1-1-2021_g0_t0.imec0.lf.bin`

    Returns:
    --------
    pathlib.Path: the re-rooted path, e.g. `/baz/qux/1-1-2021/SpikeGLX/1-1-2021_g0/1-1-2021_g0_imec0/1-1-2021_g0_t0.imec0.lf.bin`
    """
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

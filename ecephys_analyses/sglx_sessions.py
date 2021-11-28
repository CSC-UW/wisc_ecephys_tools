"""
These functions resolve paths to SpikeGLX data, assuming that the data are
organized 'session-style' and described using the sglx_sessions.yaml format.

Session style organization looks like this:
- subject_dir/ (e.g. ANPIX11-Adrian/)*
    - session_dir/ (e.g. 8-27-2021/)
        - SpikeGLX/ (aka "session_sglx_dir")
            - gate_dir/ (example: 8-27-2021_g0/)
            ...
            - gate_dir/ (example: 8-27-2021_Z_g0)

* A subject directory is not strictly necessary, but is typical.

The sglx_sessions.yaml consists of several 'YAML documents' (collectively
called a 'YAML stream'), each of which describes whee the data for one
subject can be found. One of these YAML documents might look like this:

---
subject: Adrian
recording_sessions:
  - id: 8-27-2021
    ap: /Volumes/neuropixel_archive/Data/chronic/CNPIX11-Adrian/8-27-2021/SpikeGLX/
    lf: /Volumes/NeuropixelNAS2/data1/CNPIX11-Adrian/8-27-2021/SpikeGLX/
  ...
  - id: 8-31-2021
    ap: /Volumes/neuropixel_archive/Data/chronic/CNPIX11-Adrian/8-31-2021/SpikeGLX/
    lf: /Volumes/NeuropixelNAS1/data/CNPIX11-Adrian/8-31-2021/SpikeGLX/
...

Note that the AP and LFP data, as well as data from different sessions, can be distributed
across different locations (e.g. different NAS devices). This is because the the sheer volume
of AP data often requires specialized storage.
"""
# TODO: It would probably be better to define a location priority list, rather than to
#       explicitly define AP and LF data locations as we do currently. This could be less
#       verbose and also allow splitting of data across locations based on factors other
#       than stream type.
import re
from itertools import chain
from pathlib import Path
import pandas as pd

from ecephys.sglx.file_mgmt import (
    filter_files,
    validate_sglx_path,
    get_gate_files,
    filelist_to_frame,
)


def get_session_style_path_parts(path):
    gate_dir, probe_dirname, fname = validate_sglx_path(path)
    session_sglx_dir = gate_dir.parent
    session_dir = session_sglx_dir.parent
    subject_dir = session_dir.parent
    return (
        subject_dir,
        session_dir.name,
        session_sglx_dir.name,
        gate_dir.name,
        probe_dirname,
        fname,
    )


def get_gate_directories(session_sglx_dir):
    """Get all gate directories belonging to a single session.

    Parameters:
    -----------
    session_sglx_dir: pathlib.Path

    Returns:
    --------
    list of pathlib.Path
    """
    matches = [
        p
        for p in session_sglx_dir.glob(f"*_g*")
        if (p.is_dir() and re.search(r"_g\d+\Z", p.name))
    ]
    return sorted(matches)


def get_session_files_from_single_location(session_sglx_dir):
    """Get all SpikeGLX files belonging to a single session directory.

    Parameters:
    -----------
    session_sglx_dir: pathlib.Path

    Returns:
    --------
    list of pathlib.Path
    """
    return list(
        chain.from_iterable(
            get_gate_files(gate_dir)
            for gate_dir in get_gate_directories(session_sglx_dir)
        )
    )


def get_session_files_from_multiple_locations(session):
    """Get all SpikeGLX files belonging to a single session.
    The AP and LF files may be stored in separate locations.

    Parameters:
    -----------
    session: dict
        From sessions.yaml, must have fields 'ap' and 'lf' pointing to respective data locations.

    Returns:
    --------
    list of pathlib.Path
    """
    ap_files = filter_files(
        get_session_files_from_single_location(Path(session["ap"])), stream="ap"
    )
    lf_files = filter_files(
        get_session_files_from_single_location(Path(session["lf"])), stream="lf"
    )
    return ap_files + lf_files


def get_subject_files(sessions):
    """Get all SpikeGLX files belonging to a single subject's YAML document.

    Parameters:
    -----------
    doc: dict
        The YAML specification for this subject.

    Returns:
    --------
    list of pathlib.Path
    """
    return list(
        chain.from_iterable(
            get_session_files_from_multiple_locations(session) for session in sessions
        )
    )


def get_yamlstream_files(stream):
    """Get SpikeGLX files of belonging to all YAML documents in a YAML stream.

    Parameters:
    -----------
    stream: list of dict
        The YAML specifications for each subject.

    Returns:
    --------
    dict of list of pathlib.Path, keyed by subject.
    """
    return {
        doc["subject"]: get_subject_files(doc["recording_sessions"]) for doc in stream
    }


def get_yamlstream_files_as_frame(stream):
    """Get SpikeGLX files of belonging to all YAML documents in a YAML stream."""
    d = {
        doc["subject"]: filelist_to_frame(get_subject_files(doc["recording_sessions"]))
        for doc in stream
    }
    return pd.concat(d.values(), keys=d.keys(), names=["subject"], sort=True)

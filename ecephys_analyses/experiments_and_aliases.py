"""
These functions resolve paths to SpikeGLX data, assuming that the data
are described according to the experiments_and_aliases.yaml format.
The data must also be organized and described 'session-style' -- for
more information, see sglx_sessions.py.

The experiments_and_aliases.yaml format allows you to define experiments
in terms of SpikeGLX recording sessions, and to refer to subsets of this
data using 'aliases'.
"""
import re
from itertools import chain

from ecephys.sglx.file_mgmt import (
    filelist_to_frame,
    loc,
    set_index,
)

from .sglx_sessions import get_session_files_from_multiple_locations
from .utils import get_subject_document


def parse_trigger_stem(stem):
    """Parse recording identifiers from a SpikeGLX style filename stem.
    Because this stem ends with the trigger identifier, we call it a
    'trigger stem'.

    Although this function may seem like it belongs in ecephys.sglx.file_mgmt,
    it really belongs here. This is because the concept of a trigger stem is
    not really used in SpikeGLX, but is used in experiments_and_aliases.yaml
    as a convenient way of specifying file ranges.

    Parameters
    ---------
    stem: str
        The filename stem to parse, e.g. "my-run-name_g0_t1"

    Returns
    -------
    run: str
        The run name, e.g. "my-run-name".
    gate: str
        The gate identifier, e.g. "g0".
    trigger: str
        The trigger identifier, e.g. "t1".

    Examples
    --------
    >>> parse_trigger_stem('3-1-2021_A_g1_t0')
    ('3-1-2021_A', 'g1', 't0')
    """
    x = re.search(r"_g\d+_t\d+\Z", stem)  # \Z forces match at string end.
    run = stem[: x.span()[0]]  # The run name is everything before the match
    gate = re.search(r"g\d+", x.group()).group()
    trigger = re.search(r"t\d+", x.group()).group()

    return (run, gate, trigger)


def get_experiment_sessions(sessions, experiment):
    """Get the subset of sessions needed by an experiment.

    Parameters:
    -----------
    sessions: list of dict
        The YAML specification of sessions for this subject.
    experiment: dict
        The YAML specification of this experiment for this subject.

    Returns:
    --------
    list of dict
    """
    return [
        session
        for session in sessions
        if session["id"] in experiment["recording_session_ids"]
    ]


def get_experiment_files(sessions, experiment):
    """Get all SpikeGLX files belonging to a single experiment.

    Parameters:
    -----------
    sessions: list of dict
        The YAML specification of sessions for this subject.
    experiment: dict
        The YAML specification of this experiment for this subject.

    Returns:
    --------
    list of pathlib.Path
    """
    files = list(
        chain.from_iterable(
            get_session_files_from_multiple_locations(session)
            for session in get_experiment_sessions(sessions, experiment)
        )
    )
    return filelist_to_frame(files)


def get_alias_files(sessions, experiment, alias):
    """Get all SpikeGLX files belonging to a single alias.

    Parameters:
    -----------
    sessions: list of dict
        The YAML specification of sessions for this subject.
    experiment: dict
        The YAML specification of this experiment for this subject.
    alias: dict
        The YAML specification of this alias, for this experiment, for this subject.

    Returns:
    --------
    pd.DataFrame:
        All files in the alias, in sorted order, inclusive of both start_file and end_file.
    """
    df = get_experiment_files(sessions, experiment)
    df = (
        set_index(df).reset_index(level=0).sort_index()
    )  # Make df sliceable using (run, gate, trigger)
    return df[
        parse_trigger_stem(alias["start_file"]) : parse_trigger_stem(alias["end_file"])
    ].reset_index()


def get_files(
    sessions_stream,
    experiments_stream,
    subject_name,
    experiment_name,
    alias_name=None,
    **kwargs,
):
    """Get all SpikeGLX files matching selection criteria.

    Parameters:
    -----------
    sessions_stream: list of dict
        The YAML specification of sessions for each subject.
    experiments_stream: list of dict
        The YAML specification of experiments and aliases for each subject.
    subject_name: string
    experiment_name: string
    alias_name: string (default: None)

    Returns:
    --------
    pd.DataFrame:
        All requested files in sorted order.
    """
    sessions_doc = get_subject_document(sessions_stream, subject_name)
    experiments_doc = get_subject_document(experiments_stream, subject_name)

    sessions = sessions_doc["recording_sessions"]
    experiment = experiments_doc["experiments"][experiment_name]

    df = (
        get_alias_files(sessions, experiment, experiment["aliases"][alias_name])
        if alias_name
        else get_experiment_files(sessions, experiment)
    )
    return loc(df, **kwargs)

"""
These functions resolve paths to SpikeGLX data, assuming that the data
are described according to the experiments_and_aliases.yaml format.
The data must also be organized and described 'session-style' -- for
more information, see sglx_sessions.py.

The experiments_and_aliases.yaml format allows you to define experiments
in terms of SpikeGLX recording sessions, and to refer to subsets of this
data using 'aliases'.

Aliases contain a list of {'start_file': <...>, 'end_file': <...>} dictionaries
each specifying a continuous subset of data.
"""
import re
from itertools import chain

import pandas as pd
from ecephys.sglx.file_mgmt import filelist_to_frame, loc, set_index

from .sessions import get_session_files_from_multiple_locations
from ..utils import get_subject_document


SUBALIAS_IDX_DF_VALUE = -1  # Value of 'subalias_idx' column when there is a single subalias.


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


def _get_subalias_files(files_df, start_file, end_file, subalias_idx=None):
    if subalias_idx is None:
        subalias_idx = SUBALIAS_IDX_DF_VALUE
    subalias_df = files_df[
            parse_trigger_stem(start_file) : parse_trigger_stem(end_file)
    ].reset_index()
    subalias_df['subalias_idx'] = subalias_idx
    return subalias_df


def get_alias_files(sessions, experiment, alias):
    """Get all SpikeGLX files belonging to a single alias.

    Parameters:
    -----------
    sessions: list of dict
        The YAML specification of sessions for this subject.
    experiment: dict
        The YAML specification of this experiment for this subject.
    alias: list
        The YAML specification of this alias, for this experiment, for this subject.
        The following formats is expected:
            [
                {
                    'start_file': <start_file_stem>
                    'end_file': <end_file_stem>
                }, # "subalias" 0
                {
                    'start_file': <start_file_stem>
                    'end_file': <end_file_stem>
                }, # "subalias" 1
                ...
            ]
        The index of the subalias each file is taken from is specified in the 'subalias_idx' column in the
        returned frame. If there is a unique subalias, subalias_idx is set to -1

    Returns:
    --------
    pd.DataFrame:
        All files in each of the sub-aliases, in sorted order, inclusive of both start_file and end_file.
    """
    df = get_experiment_files(sessions, experiment)
    df = (
        set_index(df).reset_index(level=0).sort_index()
    )  # Make df sliceable using (run, gate, trigger)

    if isinstance(alias, list) and len(alias) == 1:  # Single subalias ("subalias_idx" is set to -1)
        _get_subalias_files(df, alias[0]['start_file'], alias[0]['end_file'], subalias_idx=None)

    elif isinstance(alias, list):  # Multiple subaliases.
        return pd.concat(
            [
                _get_subalias_files(df, subalias['start_file'], subalias['end_file'], subalias_idx=i)
                for i, subalias in enumerate(alias)
            ]
        ).reset_index()
    
    else:
        raise ValueError("Unrecognized format for alias:\n {alias}")


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

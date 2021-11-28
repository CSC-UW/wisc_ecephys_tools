import re
from itertools import chain

from ecephys.sglx.file_mgmt import (
    filelist_to_frame,
    loc,
    set_index,
)

from .sglx_sessions import (
    get_subject_document,
    _get_session_files_from_multiple_locations,
)

# This function seems like it belongs in file_mgmt.py, since it does not
# rely on sessions.yaml or experiments_and_aliases.yaml, but it actually does.
# The trigger stem really on exists in the context of the e&a file.
def parse_trigger_stem(stem):
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


def _get_experiment_files(sessions, experiment):
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
    return list(
        chain.from_iterable(
            _get_session_files_from_multiple_locations(session)
            for session in get_experiment_sessions(sessions, experiment)
        )
    )


def get_experiment_files(sessions, experiment):
    return filelist_to_frame(_get_experiment_files(sessions, experiment))


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
    **kwargs
):
    """Get all SpikeGLX files matching selection criteria."""
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

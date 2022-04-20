import pandas as pd
from hypnogram import DatetimeHypnogram, load_datetime_hypnogram

from ecephys_project_manager import get_lfp_bin_paths, get_project_counterparts

## HYPNOGRAM

def load_and_concatenate_second_hypnograms(
    subject, experiment, alias, extension=".hypnogram.tsv", project="Scoring",
):
    """Return concatenated hypnograms with start/end_time fields in datetime.
    
    Return hypno from for the first probe (<imec10) from which we find all hypnograms.
    Raise FileNotFoundError if at least one of the hypnograms is missing.
    
    Returns:
    --------
    pd.DataFrame: Concatenated hypnogram with 'start_time', 'end_time',
        'duration' columns as seconds, and 'start_time_datetime',
        'end_time_datetime', 'duration_datetime' columns as datetime.datetime
        objects.
    """
    hyp = load_and_concatenate_datetime_hypnograms(
        subject, experiment, alias, extension=extension, project=project,
    )
    hyp['start_time_datetime'] = hyp['start_time']
    hyp['end_time_datetime'] = hyp['end_time']
    hyp['duration_datetime'] = hyp['duration']
    # Convert to seconds
    rec_start_datetime = hyp.iloc[0]['start_time_datetime']
    hyp['start_time'] = (hyp['start_time_datetime'] - rec_start_datetime).dt.total_seconds()
    hyp['end_time'] = (hyp['end_time_datetime'] - rec_start_datetime).dt.total_seconds()
    hyp['duration'] = hyp['duration_datetime'].dt.total_seconds()

    return hyp


def load_and_concatenate_datetime_hypnograms(
    subject, experiment, alias, extension=".hypnogram.tsv", project="Scoring",
):
    """Return concatenated hypnograms with start/end_time fields in datetime.
    
    Return hypno from for the first probe (<imec10) from which we find all hypnograms.
    Raise FileNotFoundError if at least one of the hypnograms is missing.
    
    Returns:
    --------
    pd.DataFrame: Concatenated hypnogram with 'start_time', 'end_time', 'duration'
        columns as datetime.datetime objects
    """

    probe_i = 0
    all_hypnograms_exist = False
    while not all_hypnograms_exist and probe_i < 10:
        probe = f'imec{probe_i}'

        lfp_paths = get_lfp_bin_paths(subject, experiment, alias, probe=probe)
        hypnogram_paths = get_project_counterparts(
            "Scoring", subject, lfp_paths, extension, remove_stream=True
        )

        hypnogram_exists = [
            (lfp_path, hypnogram_path)
            for lfp_path, hypnogram_path in zip(lfp_paths, hypnogram_paths)
            if hypnogram_path.is_file()
        ]
        all_hypnograms_exist = len(hypnogram_exists) == len(lfp_paths)
        probe_i += 1

    if not all_hypnograms_exist:
        raise FileNotFoundError("Missing hypnograms for {subject}, {experiment}, {alias}.")

    lfp_paths, hypnogram_paths = map(list, zip(*hypnogram_exists))
    hypnograms = [load_datetime_hypnogram(path) for path in hypnogram_paths]
    datetime_hypnogram = pd.concat(hypnograms).reset_index(drop=True)

    return datetime_hypnogram

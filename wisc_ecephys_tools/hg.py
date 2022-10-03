from ecephys.hypnogram.hypnogram import FloatHypnogram
import pandas as pd
from ecephys.hypnogram import load_datetime_hypnogram
from wisc_ecephys_tools import get_lfp_bin_paths, get_lfp_bin_table, get_project_counterparts

# TODO: Is this module used? Nobody seems to have noticed that imports were incorrect, and contents are not imported to the top-level

## HYPNOGRAM


def load_hypnogram_as_generic_events(
    subject,
    experiment,
    alias,
    extension=".hypnogram.tsv",
    project="scoring",
):
    """Load and concatenate second hypnograms. Add t1/t2/description fields.

    Description field contains f"{state}: {start_time}(s) - {end_time}(s)"
    """
    hyp = load_and_concatenate_second_hypnograms(
        subject,
        experiment,
        alias,
        extension=extension,
        project=project,
    )
    hyp["t1"] = hyp["start_time"]
    hyp["t2"] = hyp["end_time"]
    hyp["description"] = (
        hyp["state"].map(str)
        + ": "
        + hyp["start_time"].round(3).map(str)
        + "(s) - "
        + hyp["end_time"].round(3).map(str)
        + "(s)"
    )

    return hyp


def get_hypnogram_probe(
    subject,
    experiment,
    alias,
    extension=".hypnogram.txt",
    project="scoring",
):
    """Return the name of the probe used for scoring an alias.
    
    Assumes the same probe was used for all alias files.
    """
    # Pull all hypnograms
    probe_i = 0
    all_hypnograms_exist = False
    # We need to try all probes
    while not all_hypnograms_exist and probe_i <= 10:
        probe = f"imec{probe_i}"
        print(probe)

        lfp_paths = get_lfp_bin_paths(subject, experiment, alias, probe=probe)

        hypnogram_paths = get_project_counterparts(
            project, subject, lfp_paths, extension, remove_stream=True
        )

        existing_hypnogram_paths = [
            hypnogram_path for hypnogram_path in hypnogram_paths
            if hypnogram_path.is_file()
        ]
        all_hypnograms_exist = len(existing_hypnogram_paths) == len(lfp_paths)

        if all_hypnograms_exist:
            break
        
        if probe_i == 10:
            raise FileNotFoundError(
                f"Tried up to imec{probe_i} and couldn't fine hypnograms for {subject}, {experiment}, {alias}."
            )
        
        probe_i += 1
    
    return probe


def load_and_concatenate_alias_second_hypnograms(
    subject,
    experiment,
    alias,
    extension=".hypnogram.txt",
    project="scoring",
):
    """Load second hypnograms in 'alias' coordinates, ignoring gaps between subaliases.
    
    The start/end times of hypnograms loaded this way match the spike times in seconds
    of the sorted alias.

    NB: Subalias files are contiguous, files real times are NOT contiguous across subaliases
    but subaliases are concatenated together (ignoring the gaps) during sorting.
    """
    probe = get_hypnogram_probe(
        subject,
        experiment,
        alias,
        extension=extension,
        project=project,
    )

    # Pull all hypnograms
    lfp_paths = get_lfp_bin_paths(subject, experiment, alias, probe=probe)
    lfp_tab = get_lfp_bin_table(subject, experiment, alias, probe=probe)

    hypnogram_paths = get_project_counterparts(
        project, subject, lfp_paths, extension, remove_stream=True
    )
    assert all([h.exists() for h in hypnogram_paths])

    # Concatenate hypnograms. Ignore gaps (look only at trigger file duration, not tExperiment or FileCreateTime)
    hyps = []
    cumulative_hypnogram_duration = 0
    for i, hyp_path in enumerate(hypnogram_paths):
        if extension == '.hypnogram.txt':
            trigger_hyp = FloatHypnogram.from_visbrain(hyp_path)
        else:
            raise NotImplementedError()
        trigger_hyp["start_time"] += cumulative_hypnogram_duration
        trigger_hyp["end_time"] += cumulative_hypnogram_duration
        # TODO: Start/end time in experiment/alias coordinates
        # trigger_hyp["start_time_experiment"] = 
        # trigger_hyp["start_time_experiment"] = 
        hyps.append(trigger_hyp)

        cumulative_hypnogram_duration += float(lfp_tab.iloc[i]["fileTimeSecs"])
    
    return pd.concat(hyps).reset_index(drop=True)
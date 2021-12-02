# Experiment-agnostic loading functions.
# TODO: Separate functions into those that only require a path
# from those that fetch paths.
import pandas as pd
from ast import literal_eval
from hypnogram import load_datetime_hypnogram
from ecephys.utils import load_df_h5
from ecephys.xrsig import load_and_concatenate_datasets

from .sglx.experiments import get_lfp_bin_paths
from .projects import get_project_counterparts


def load_sr_chans(path):
    df = pd.read_csv(path)
    df.sr_chans = df.sr_chans.apply(
        lambda x: [] if pd.isnull(x) else list(literal_eval(x))
    )

    return df


def _get_abs_sink(spws):
    _spws = spws.copy()
    _spws["sink_amplitude"] = spws["sink_amplitude"].abs()
    _spws["sink_integral"] = spws["sink_integral"].abs()
    return _spws


def load_and_concatenate_spws(subject, experiment, alias, probe, abs_sink=False):
    bin_paths = get_lfp_bin_paths(subject, experiment, alias, probe=probe)
    spw_paths = get_project_counterparts("SPWRs", subject, bin_paths, "spws.h5")
    spws = [load_df_h5(path) for path in spw_paths]

    for _spws in spws:
        file_start = pd.to_datetime(_spws.attrs["file_start"])
        if _spws.empty:
            continue
        _spws["start_time"] = file_start + pd.to_timedelta(_spws["start_time"], "s")
        _spws["end_time"] = file_start + pd.to_timedelta(_spws["end_time"], "s")
        _spws["midpoint"] = file_start + pd.to_timedelta(_spws["midpoint"], "s")

    combined_spws = pd.concat(spws).reset_index(drop=True)
    combined_spws.index += 1
    combined_spws.index = combined_spws.index.rename("spw_number")

    if abs_sink:
        combined_spws = _get_abs_sink(combined_spws)

    return combined_spws


def load_and_concatenate_hypnograms(subject, experiment, alias, probe):
    bin_paths = get_lfp_bin_paths(subject, experiment, alias, probe=probe)
    hypnogram_paths = get_project_counterparts(
        "SPWRs", subject, bin_paths, "hypnogram.tsv"
    )
    hypnograms = [load_datetime_hypnogram(path) for path in hypnogram_paths]
    return pd.concat(hypnograms).reset_index(drop=True)


def load_and_concatenate_spectrograms(subject, experiment, alias, probe):
    bin_paths = get_lfp_bin_paths(subject, experiment, alias, probe=probe)
    dataset_paths = get_project_counterparts("SPWRs", subject, bin_paths, "spg.nc")
    return load_and_concatenate_datasets(dataset_paths)


def load_and_concatenate_bandpowers(subject, experiment, alias, probe):
    bin_paths = get_lfp_bin_paths(subject, experiment, alias, probe=probe)
    dataset_paths = get_project_counterparts(
        "SPWRs", subject, bin_paths, "bandpower.nc"
    )
    return load_and_concatenate_datasets(dataset_paths)

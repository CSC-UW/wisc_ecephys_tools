import pandas as pd
import xarray as xr
from ast import literal_eval
from ecephys.scoring import load_datetime_hypnogram
from ecephys.utils import load_df_h5, all_equal

from .paths import get_sglx_style_datapaths


def load_sr_chans(path):
    df = pd.read_csv(path)
    df.sr_chans = df.sr_chans.apply(
        lambda x: [] if pd.isnull(x) else list(literal_eval(x))
    )

    return df


def load_power(subject, experiment, condition, ext):
    power_paths = get_sglx_style_datapaths(
        subject=subject, experiment=experiment, condition=condition, ext=ext
    )

    powers = list()
    for path in power_paths:
        try:
            powers.append(xr.open_dataset(path))
        except FileNotFoundError:
            pass

    for p in powers:
        if "file_start" in p.attrs:
            file_start = p.file_start
        else:
            file_starts = [da.file_start for (da_name, da) in p.items()]
            assert all_equal(file_starts), "Power series start times should match."
            file_start = file_starts[0]
        p["time"] = pd.to_datetime(file_start) + pd.to_timedelta(p.time.values, "s")

    return xr.concat(powers, dim="time")


def load_bandpower(subject, experiment, condition, ext="bandpower.nc"):
    return load_power(subject, experiment, condition, ext)


def load_spectrogram(subject, experiment, condition):
    return load_power(subject, experiment, condition, "spg2.nc")


def load_hypnogram(subject, experiment, condition):
    hypnogram_paths = get_sglx_style_datapaths(
        subject=subject, experiment=experiment, condition=condition, ext="hypnogram.tsv"
    )
    hypnograms = [load_datetime_hypnogram(path) for path in hypnogram_paths]
    return pd.concat(hypnograms).reset_index(drop=True)


def load_spws(subject, experiment, condition, condition_start_dt=None):
    spw_paths = get_sglx_style_datapaths(
        subject=subject, experiment=experiment, condition=condition, ext="spws.h5"
    )
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

    if condition_start_dt:
        combined_spws["time_from_condition_start"] = (
            combined_spws["start_time"] - condition_start_dt
        )

    return combined_spws
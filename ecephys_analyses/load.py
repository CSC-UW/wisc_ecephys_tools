import pandas as pd
import xarray as xr
from ast import literal_eval
from hypnogram import load_datetime_hypnogram
from ecephys.utils import load_df_h5
from ecephys.signal.xarray_utils import rebase_time

from .paths import get_sglx_style_datapaths

SLEEP_HOMEOSTASIS = "sleep-homeostasis"
NREM = ["N1", "N2"]
LIGHTS_ON = "09:00:00"
LIGHTS_OFF = "21:00:00"

### Experiment-agnostic loading functions.


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
            powers.append(xr.load_dataset(path))
        except FileNotFoundError:
            pass

    return rebase_time(xr.concat(powers, dim="time"))


def load_bandpower(subject, experiment, condition, ext="bandpower.nc"):
    return load_power(subject, experiment, condition, ext)


def load_spectrogram(subject, experiment, condition):
    return load_power(subject, experiment, condition, "spg.nc")


def load_hypnogram(subject, experiment, condition):
    hypnogram_paths = get_sglx_style_datapaths(
        subject=subject, experiment=experiment, condition=condition, ext="hypnogram.tsv"
    )
    hypnograms = [load_datetime_hypnogram(path) for path in hypnogram_paths]
    return pd.concat(hypnograms).reset_index(drop=True)


def _get_abs_sink(spws):
    _spws = spws.copy()
    _spws["sink_amplitude"] = spws["sink_amplitude"].abs()
    _spws["sink_integral"] = spws["sink_amplitude"].abs()
    return _spws


def load_spws(subject, experiment, condition, condition_start_dt=None, abs_sink=False):
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

    if abs_sink:
        combined_spws = _get_abs_sink(combined_spws)

    return combined_spws


### Sleep-homeostasis experiment specific loading functions.


def load_baseline_light_period_nrem(subject, abs_sink=False):
    condition = "light-period-circadian-match"
    hyp = load_hypnogram(subject, SLEEP_HOMEOSTASIS, condition)
    hyp = hyp.keep_states(NREM).keep_between(LIGHTS_ON, LIGHTS_OFF)
    spws = load_spws(subject, SLEEP_HOMEOSTASIS, condition, abs_sink=abs_sink)
    spws = spws[hyp.covers_time(spws.start_time)]
    return hyp, spws


def load_early_recovery_nrem(subject, abs_sink=False):
    condition = "recovery-sleep"
    duration = "01:00:00"
    hyp = load_hypnogram(subject, SLEEP_HOMEOSTASIS, condition)
    hyp = hyp.keep_states(NREM).keep_first(duration)
    spws = load_spws(subject, SLEEP_HOMEOSTASIS, condition, abs_sink=abs_sink)
    spws = spws[hyp.covers_time(spws.start_time)]
    return hyp, spws


def load_late_recovery_nrem(subject, abs_sink=False):
    condition = "recovery-sleep"
    duration = "01:00:00"
    hyp = load_hypnogram(subject, SLEEP_HOMEOSTASIS, condition)
    hyp = hyp.keep_states(NREM).keep_last(duration)
    spws = load_spws(subject, SLEEP_HOMEOSTASIS, condition, abs_sink=abs_sink)
    spws = spws[hyp.covers_time(spws.start_time)]
    return hyp, spws


def load_first2h_recovery_nrem(subject, abs_sink=False):
    condition = "recovery-sleep"
    duration = "02:00:00"
    hyp = load_hypnogram(subject, SLEEP_HOMEOSTASIS, condition)
    hyp = hyp.keep_states(NREM).keep_first(duration)
    spws = load_spws(subject, SLEEP_HOMEOSTASIS, condition, abs_sink=abs_sink)
    spws = spws[hyp.covers_time(spws.start_time)]
    return hyp, spws


def load_first2h_recovery_match_nrem(subject, rec_hyp, abs_sink=False):
    condition = "recovery-sleep-circadian-match"
    duration = "02:00:00"
    hyp = load_hypnogram(subject, SLEEP_HOMEOSTASIS, condition)
    hyp = (
        hyp.keep_states(NREM)
        .keep_between(rec_hyp.start_time.min().strftime("%H:%M:%S"), LIGHTS_OFF)
        .keep_first(duration)
    )
    spws = load_spws(subject, SLEEP_HOMEOSTASIS, condition, abs_sink=abs_sink)
    spws = spws[hyp.covers_time(spws.start_time)]
    return hyp, spws


def load_recovery_nrem(subject, abs_sink=False):
    condition = "recovery-sleep"
    hyp = load_hypnogram(subject, SLEEP_HOMEOSTASIS, condition)
    hyp = hyp.keep_states(NREM).keep_between(LIGHTS_ON, LIGHTS_OFF)
    spws = load_spws(subject, SLEEP_HOMEOSTASIS, condition, abs_sink=abs_sink)
    spws = spws[hyp.covers_time(spws.start_time)]
    return hyp, spws


def load_deprivation(subject, abs_sink=False):
    condition = "extended-wake"
    hyp = load_hypnogram(subject, SLEEP_HOMEOSTASIS, condition)
    spws = load_spws(subject, SLEEP_HOMEOSTASIS, condition, abs_sink=abs_sink)
    return hyp, spws
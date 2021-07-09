import pandas as pd
import xarray as xr
from ast import literal_eval
from ecephys.utils import load_df_h5
from ecephys.signal.xarray_utils import rebase_time

from ..paths import get_sglx_style_datapaths

SLEEP_HOMEOSTASIS = "sleep-homeostasis"
NREM = ["N1", "N2"]
WAKE = ["Wake", "aWk", "qWk"]
SPW_STATES = NREM + WAKE + ["Trans", "IS", "Arousal"]
LIGHTS_ON = "09:00:00"
LIGHTS_OFF = "21:00:00"
LIGHT_PERIOD = (LIGHTS_ON, LIGHTS_OFF)

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


def _get_abs_sink(spws):
    _spws = spws.copy()
    _spws["sink_amplitude"] = spws["sink_amplitude"].abs()
    _spws["sink_integral"] = spws["sink_integral"].abs()
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


def load_sleep_homeostasis_spws(
    subject,
    condition,
    keep_states=None,
    keep_between=None,
    keep_first=None,
    keep_last=None,
    abs_sink=False,
):
    assert not (
        keep_first and keep_last
    ), "Only one of keep_first or keep_last can be provided."
    hyp = load_hypnogram(subject, SLEEP_HOMEOSTASIS, condition)
    hyp = hyp.keep_states(keep_states) if keep_states else hyp
    hyp = hyp.keep_between(*keep_between) if keep_between else hyp
    hyp = hyp.keep_first(keep_first) if keep_first else hyp
    hyp = hyp.keep_last(keep_last) if keep_last else hyp
    spws = load_spws(subject, SLEEP_HOMEOSTASIS, condition, abs_sink=abs_sink)
    spws = spws[hyp.covers_time(spws.start_time)]
    return hyp, spws


def load_baseline_light_period(subject, keep_states=SPW_STATES, abs_sink=False):
    return load_sleep_homeostasis_spws(
        subject,
        "light-period-circadian-match",
        keep_states=keep_states,
        keep_between=LIGHT_PERIOD,
        abs_sink=abs_sink,
    )


def load_baseline_light_period_nrem(subject, abs_sink=False):
    return load_baseline_light_period(subject, keep_states=NREM, abs_sink=abs_sink)


def load_early_recovery(subject, keep_states=SPW_STATES, abs_sink=False):
    return load_sleep_homeostasis_spws(
        subject,
        "recovery-sleep",
        keep_states=keep_states,
        keep_first="01:00:00",
        abs_sink=abs_sink,
    )


def load_early_recovery_nrem(subject, abs_sink=False):
    return load_early_recovery(subject, keep_states=NREM, abs_sink=abs_sink)


def load_late_recovery(subject, keep_states=SPW_STATES, abs_sink=False):
    return load_sleep_homeostasis_spws(
        subject,
        "recovery-sleep",
        abs_sink=abs_sink,
        keep_states=keep_states,
        keep_last="01:00:00",
    )


def load_late_recovery_nrem(subject, abs_sink=False):
    return load_late_recovery(subject, keep_states=NREM, abs_sink=abs_sink)


def load_first2h_recovery(subject, keep_states=SPW_STATES, abs_sink=False):
    return load_sleep_homeostasis_spws(
        subject,
        "recovery-sleep",
        abs_sink=abs_sink,
        keep_states=keep_states,
        keep_first="02:00:00",
    )


def load_first2h_recovery_nrem(subject, abs_sink=False):
    return load_first2h_recovery(subject, keep_states=NREM, abs_sink=abs_sink)


def load_first2h_recovery_match(
    subject, recovery_hypnogram, keep_states=SPW_STATES, abs_sink=False
):
    recovery_nrem_start = recovery_hypnogram.start_time.min().strftime("%H:%M:%S")
    return load_sleep_homeostasis_spws(
        subject,
        "recovery-sleep-circadian-match",
        abs_sink=abs_sink,
        keep_states=keep_states,
        keep_between=(recovery_nrem_start, LIGHTS_OFF),
        keep_first="02:00:00",
    )


def load_first2h_recovery_match_nrem(subject, recovery_hypnogram, abs_sink=False):
    return load_first2h_recovery_match(
        subject, recovery_hypnogram, keep_states=NREM, abs_sink=abs_sink
    )


def load_recovery(subject, keep_states=SPW_STATES, abs_sink=False):
    return load_sleep_homeostasis_spws(
        subject,
        "recovery-sleep",
        abs_sink=abs_sink,
        keep_states=keep_states,
        keep_between=LIGHT_PERIOD,
    )


def load_recovery_nrem(subject, abs_sink=False):
    return load_recovery(subject, keep_states=NREM, abs_sink=abs_sink)


def load_deprivation(subject, keep_states=WAKE, abs_sink=False):
    return load_sleep_homeostasis_spws(
        subject,
        "extended-wake",
        abs_sink=abs_sink,
    )


def load_early_deprivation(subject, keep_states=WAKE, abs_sink=False):
    return load_sleep_homeostasis_spws(
        subject,
        "extended-wake",
        abs_sink=abs_sink,
        keep_states=keep_states,
        keep_first="01:00:00",
    )


def load_late_deprivation(subject, keep_states=WAKE, abs_sink=False):
    return load_sleep_homeostasis_spws(
        subject,
        "extended-wake",
        abs_sink=abs_sink,
        keep_states=keep_states,
        keep_last="01:00:00",
    )
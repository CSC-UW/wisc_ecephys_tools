from hypnogram.hypnogram import DatetimeHypnogram
from .load import (
    load_hypnogram as _load_hypnogram,
    load_spws as _load_spws,
    load_spectrogram as _load_spectrogram,
)

SLEEP_HOMEOSTASIS = "sleep-homeostasis"
NREM = ["N1", "N2"]
WAKE = ["Wake", "aWk", "qWk"]
SPW_STATES = NREM + WAKE + ["Trans", "IS", "Arousal"]
LIGHTS_ON = "09:00:00"
LIGHTS_OFF = "21:00:00"

DELTA = (0.5, 4)


def _get_recovery_sleep_start_time(subject):
    recovery = (
        _load_hypnogram(subject, SLEEP_HOMEOSTASIS, "recovery-sleep")
        .keep_states(NREM)
        .keep_between(LIGHTS_ON, LIGHTS_OFF)
    )

    return recovery.start_time.min().strftime("%H:%M:%S")


def _load_recovery(subject, keep_states=SPW_STATES):
    recovery_start = _get_recovery_sleep_start_time(subject)
    return (
        _load_hypnogram(subject, SLEEP_HOMEOSTASIS, "recovery-sleep")
        .keep_states(keep_states)
        .keep_between(recovery_start, LIGHTS_OFF)
    )


def _load_early_recovery(subject, keep_states=SPW_STATES):
    recovery = _load_recovery(subject, keep_states)
    return recovery.keep_first("01:00:00")


def _load_late_recovery(subject, keep_states=SPW_STATES):
    recovery = _load_recovery(subject, keep_states)
    return recovery.keep_last("01:00:00")


def _load_first2h_recovery(subject, keep_states=SPW_STATES):
    recovery = _load_recovery(subject, keep_states)
    return recovery.keep_first("02:00:00")


def _load_baseline_light_period(subject, keep_states=SPW_STATES):
    return (
        _load_hypnogram(subject, SLEEP_HOMEOSTASIS, "light-period-circadian-match")
        .keep_states(keep_states)
        .keep_between(LIGHTS_ON, LIGHTS_OFF)
    )


def _load_first2h_recovery_match(subject, keep_states=SPW_STATES):
    recovery_start = _get_recovery_sleep_start_time(subject)
    baseline = _load_baseline_light_period(subject, keep_states)
    return baseline.keep_between(recovery_start, LIGHTS_OFF).keep_first("02:00:00")


def _load_deprivation(subject, keep_states=WAKE):
    return (
        _load_hypnogram(subject, SLEEP_HOMEOSTASIS, "extended-wake")
        .keep_states(keep_states)
        .keep_between(LIGHTS_ON, LIGHTS_OFF)
    )


def _load_early_deprivation(subject, keep_states=WAKE):
    return _load_deprivation(subject, keep_states).keep_first("01:00:00")


def _load_late_deprivation(subject, keep_states=WAKE):
    return _load_deprivation(subject, keep_states).keep_last("01:00:00")


_hypnogram_loaders = {
    "recovery-sleep": {
        "recovery": _load_recovery,
        "early-recovery": _load_early_recovery,
        "late-recovery": _load_late_recovery,
        "first2h-recovery": _load_first2h_recovery,
    },
    "light-period-circadian-match": {
        "baseline-light-period": _load_baseline_light_period,
        "first2h-recovery-match": _load_first2h_recovery_match,
    },
    "extended-wake": {
        "deprivation": _load_deprivation,
        "early-deprivation": _load_early_deprivation,
        "late-deprviation": _load_late_deprivation,
    },
}


def _get_hypnogram_loader(subcondition):
    for condition, subcondition_loaders in _hypnogram_loaders.items():
        if subcondition in subcondition_loaders:
            return subcondition_loaders[subcondition]


def _get_parent_condition(subcondition):
    for condition, subcondition_loaders in _hypnogram_loaders.items():
        if subcondition in subcondition_loaders:
            return condition


def load_hypnogram(subject, subcondition, **kwargs):
    loader = _get_hypnogram_loader(subcondition)
    return loader(subject, **kwargs)


def load_spws(subject, subcondition, hypnogram, **kwargs):
    spws = _load_spws(
        subject, SLEEP_HOMEOSTASIS, _get_parent_condition(subcondition), **kwargs
    )
    return spws[hypnogram.covers_time(spws.start_time)]


def load_spectrogram(subject, subcondition, hypnogram):
    spg = _load_spectrogram(
        subject, SLEEP_HOMEOSTASIS, _get_parent_condition(subcondition)
    )
    assert isinstance(hypnogram, DatetimeHypnogram)
    return (
        spg.where(hypnogram.covers_time(spg.datetime))
        .dropna(dim="time")
        .swap_dims({"time": "datetime"})
        .drop_vars(["time", "timedelta"])
    )


def load_bands(subject, subcondition, hypnogram, bands):
    spg = load_spectrogram(subject, subcondition, hypnogram)
    return [spg.sel(frequency=slice(*band)).sum(dim="frequency") for band in bands]


def load_band(subject, subcondition, hypnogram, band):
    spg = load_spectrogram(subject, subcondition, hypnogram)
    return spg.sel(frequency=slice(*band)).sum(dim="frequency")

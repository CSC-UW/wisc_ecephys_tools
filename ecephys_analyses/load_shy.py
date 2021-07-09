from .load import load_hypnogram, load_spws

SLEEP_HOMEOSTASIS = "sleep-homeostasis"
NREM = ["N1", "N2"]
WAKE = ["Wake", "aWk", "qWk"]
SPW_STATES = NREM + WAKE + ["Trans", "IS", "Arousal"]
LIGHTS_ON = "09:00:00"
LIGHTS_OFF = "21:00:00"


def get_recovery_sleep_start_time(subject):
    recovery = (
        load_hypnogram(subject, SLEEP_HOMEOSTASIS, "recovery-sleep")
        .keep_states(NREM)
        .keep_between(LIGHTS_ON, LIGHTS_OFF)
    )

    return recovery.start_time.min().strftime("%H:%M:%S")


def load_recovery(subject, keep_states=SPW_STATES):
    recovery_start = get_recovery_sleep_start_time(subject)
    return (
        load_hypnogram(subject, SLEEP_HOMEOSTASIS, "recovery-sleep")
        .keep_states(keep_states)
        .keep_between(recovery_start, LIGHTS_OFF)
    )


def load_early_recovery(subject, keep_states=SPW_STATES):
    recovery = load_recovery(subject, keep_states)
    return recovery.keep_first("01:00:00")


def load_late_recovery(subject, keep_states=SPW_STATES):
    recovery = load_recovery(subject, keep_states)
    return recovery.keep_last("01:00:00")


def load_first2h_recovery(subject, keep_states=SPW_STATES):
    recovery = load_recovery(subject, keep_states)
    return recovery.keep_first("02:00:00")


def load_baseline_light_period(subject, keep_states=SPW_STATES):
    return (
        load_hypnogram(subject, SLEEP_HOMEOSTASIS, "light-period-circadian-match")
        .keep_states(keep_states)
        .keep_between(LIGHTS_ON, LIGHTS_OFF)
    )


def load_first2h_recovery_match(subject, keep_states=SPW_STATES):
    recovery_start = get_recovery_sleep_start_time(subject)
    baseline = load_baseline_light_period(subject, keep_states)
    return baseline.keep_between(recovery_start, LIGHTS_OFF).keep_first("02:00:00")


def load_deprivation(subject, keep_states=WAKE):
    return (
        load_hypnogram(subject, SLEEP_HOMEOSTASIS, "extended-wake")
        .keep_states(keep_states)
        .keep_between(LIGHTS_ON, LIGHTS_OFF)
    )


def load_early_deprivation(subject, keep_states=WAKE):
    return load_deprivation(subject, keep_states).keep_first("01:00:00")


def load_late_deprivation(subject, keep_states=WAKE):
    return load_deprivation(subject, keep_states).keep_last("01:00:00")


def load_all_spws(subject, abs_sink=False):
    return load_spws(subject, SLEEP_HOMEOSTASIS, "all", abs_sink)


def load_and_filter_spws(subject, hypnogram, abs_sink=False):
    spws = load_all_spws(subject, abs_sink)
    return spws[hypnogram.covers_time(spws.start_time)]

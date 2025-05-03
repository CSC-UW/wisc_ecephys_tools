"""
This module contains functions for getting hypnograms that cover different
periods and states of interest. For example, the light/dark periods, the sleep
deprivation period, recovery NREM sleep, etc.

The `scoring` module, on the other hand, contains functions for getting a total
experiment hypnogram, from which the hypnograms in this module are derived.
TODO: Maybe these modules should be named `exp_hg` and `cnd_hg`.

Note 1:
    Various calls to wne.SGLXSubject.dt2t pass "imec0" as the probe.
    This is a hack/shortcut, to ensure that the times returned by dt2t are in the
    experiment's canonical (synced) timebase. The biggest drawback of this approach is
    that imec0 needs to be available. If it were not, we'd have to:
    - Take `probe` as an argument.
    - Create a time synchronizer object, and use that to convert the output of dt2t.
"""

import itertools as it
import warnings

import matplotlib.pyplot as plt
import pandas as pd

from ecephys import hypnogram, wne
from wisc_ecephys_tools import core
from wisc_ecephys_tools.rats.constants import SleepDeprivationExperiments as Exps


def get_light_dark_periods(
    experiment: str, subject: wne.sglx.SGLXSubject, as_float: bool = True
):
    """Get light/dark periods in chronological order.

    Examples:
    ---------
    "lightsOn": [t1, t3, t5],
    "lightsOff": [t2, t4],
    -->
    intervals = [(t1, t2), (t2, t3), (t3, t4), (t4, t5)]
    labels = ["on", "off", "on", "off"]
    """
    s3 = core.get_shared_project()
    params = s3.load_experiment_subject_params(experiment, subject.name)
    on = pd.DataFrame(
        {"time": [pd.to_datetime(x) for x in params["lightsOn"]], "transition": "on"}
    )
    off = pd.DataFrame(
        {"time": [pd.to_datetime(x) for x in params["lightsOff"]], "transition": "off"}
    )
    df = pd.concat([on, off]).sort_values("time").reset_index(drop=True)
    if as_float:
        df["time"] = subject.dt2t(experiment, "imec0", df["time"].values)
        # See Note 1 above.

    periods = list(it.pairwise(df.itertuples()))
    intervals = [(start.time, end.time) for start, end in periods]
    labels = [start.transition for start, _ in periods]
    return intervals, labels


def plot_lights_overlay(
    intervals: list[tuple],
    interval_labels: list[str],
    ax: plt.Axes,
    ymin=1.0,
    ymax=1.02,
    alpha=1.0,
    zorder=1000,
    colors={"on": "yellow", "off": "gray"},  # Keys are from interval_labels
):
    """Take intervals and labels, as returned by `get_light_dark_periods()`, and use these to overlay
    the light/dark cycle onto a plot.

    Examples
    --------
    >>> fig, ax = plt.subplots()
    Overlay into background, span whole plot axis
    >>> plot_lights_overlay(intervals, interval_labels, ax=ax, ymin=0, ymax=1, alpha=0.3)
    Overlay into foreground, outside of plot yaxis (but within plot xaxis)
    >>> plot_lights_overlay(intervals, interval_labels, ax=ax, ymin=1.0, ymax=1.02, alpha=1.0)
    """
    xlim = ax.get_xlim()

    for (tOn, tOff), lbl in zip(intervals, interval_labels):
        # clip manually on xaxis so we can set clip_on=False for yaxis
        tOn = max(tOn, xlim[0])
        tOff = min(tOff, xlim[1])
        ax.axvspan(
            tOn,
            tOff,
            alpha=alpha,
            color=colors[lbl],
            zorder=zorder,
            ec="none",
            ymin=ymin,
            ymax=ymax,
            clip_on=False,
        )

    ax.set_xlim(xlim)


def get_novel_objects_period(
    experiment: str, subject: wne.sglx.SGLXSubject
) -> tuple[float, float]:
    s3 = core.get_shared_project()
    params = s3.load_experiment_subject_params(experiment, subject.name)

    start = pd.to_datetime(params["novel_objects_start"])
    start = subject.dt2t(experiment, "imec0", start)  # See Note 1 above.

    end = pd.to_datetime(params["novel_objects_end"])
    end = subject.dt2t(experiment, "imec0", end)  # See Note 1 above.

    return (start, end)


def get_novel_objects_hypnogram(
    full_hg: hypnogram.FloatHypnogram, experiment: str, subject: wne.sglx.SGLXSubject
) -> hypnogram.FloatHypnogram:
    (nod_start, nod_end) = get_novel_objects_period(experiment, subject)
    return full_hg.trim(nod_start, nod_end)


def get_day1_hypnogram(
    full_hg: hypnogram.FloatHypnogram,
    experiment: str,
    subject: wne.sglx.SGLXSubject,
) -> hypnogram.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[0][0],  # start of first light period,
        intervals[1][1],  # end of first dark period
    )


def get_day2_hypnogram(
    full_hg: hypnogram.FloatHypnogram,
    experiment: str,
    subject: wne.sglx.SGLXSubject,
) -> hypnogram.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[2][0],  # start of first light period,
        intervals[3][1],  # end of first dark period
    )


def get_day1_light_period_hypnogram(
    full_hg: hypnogram.FloatHypnogram,
    experiment: str,
    subject: wne.sglx.SGLXSubject,
) -> hypnogram.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[0][0],  # start of first light period
        intervals[0][1],  # end of first light period
    )


def get_day1_dark_period_hypnogram(
    full_hg: hypnogram.FloatHypnogram,
    experiment: str,
    subject: wne.sglx.SGLXSubject,
) -> hypnogram.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[1][0],  # start of first dark period
        intervals[1][1],  # end of first dark period
    )


def get_day2_light_period_hypnogram(
    full_hg: hypnogram.FloatHypnogram,
    experiment: str,
    subject: wne.sglx.SGLXSubject,
) -> hypnogram.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[2][0],  # start of second light period
        intervals[2][1],  # end of second light period
    )


def get_day2_dark_period_hypnogram(
    full_hg: hypnogram.FloatHypnogram,
    experiment: str,
    subject: wne.sglx.SGLXSubject,
) -> hypnogram.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[3][0],  # start of second dark period
        intervals[3][1],  # end of second dark period
    )


def get_post_deprivation_day2_light_period_hypnogram(
    full_hg: hypnogram.FloatHypnogram,
    experiment: str,
    subject: wne.sglx.SGLXSubject,
    sleep_deprivation_end: float,
) -> hypnogram.FloatHypnogram:
    d2lp_hg = get_day2_light_period_hypnogram(full_hg, experiment, subject)
    return d2lp_hg.trim(sleep_deprivation_end, d2lp_hg["end_time"].max())


def get_circadian_match_hypnogram(
    full_hg: hypnogram.FloatHypnogram, start: float, end: float
) -> hypnogram.FloatHypnogram:
    match_start = start - pd.to_timedelta("24h").total_seconds()
    match_end = end - pd.to_timedelta("24h").total_seconds()
    return full_hg.trim(match_start, match_end)


def get_conveyor_over_water_period(
    experiment: str, wne_subject: wne.sglx.SGLXSubject
) -> tuple[float, float]:
    s3 = core.get_shared_project()
    params = s3.load_experiment_subject_params(experiment, wne_subject.name)

    start = pd.to_datetime(params["conveyor_over_water_start"])
    start = wne_subject.dt2t(experiment, "imec0", start)  # See Note 1 above.

    end = pd.to_datetime(params["conveyor_over_water_end"])
    end = wne_subject.dt2t(experiment, "imec0", end)  # See Note 1 above.

    return (start, end)


def get_sleep_deprivation_period(
    experiment: str, wne_subject: wne.sglx.SGLXSubject
) -> tuple[float, float]:
    if experiment == Exps.NOD:
        return get_novel_objects_period(experiment, wne_subject)
    if experiment == Exps.COW:
        return get_conveyor_over_water_period(experiment, wne_subject)
    if experiment == Exps.CTN:
        start = min(get_conveyor_over_water_period(experiment, wne_subject))
        end = max(get_novel_objects_period(experiment, wne_subject))
        return start, end


def get_extended_wake_hypnogram(
    full_hg: hypnogram.FloatHypnogram,
    experiment: str,
    wne_subject: wne.sglx.SGLXSubject,
    minimum_endpoint_bout_duration: float = 120,
    maximum_antistate_bout_duration: float = 90,
    minimum_fraction_of_final_match: float = 0.95,
) -> hypnogram.FloatHypnogram:
    """See ecephys.hypnogram.core.Hypnogram.get_consolidated."""
    sd_start, sd_end = get_sleep_deprivation_period(experiment, wne_subject)
    five_minutes = pd.to_timedelta("5m").total_seconds()
    is_nod = (full_hg["start_time"] >= (sd_start - five_minutes)) & (
        full_hg["end_time"] <= sd_end
    )  # Note that this is a very strict criterion
    is_nodata = full_hg["state"] == "NoData"

    # Temporarily relabel NoData during SD, since we KNOW it is actually wake, and we want the algorithm that finds consolidated wake to account for this.
    full_hg.loc[is_nod & is_nodata, "state"] = "NoDataWake"
    matches = full_hg.get_consolidated(
        ["Wake", "Artifact", "Other", "NoDataWake"],
        minimum_time=(sd_end - sd_start) * 0.8,
        minimum_endpoint_bout_duration=minimum_endpoint_bout_duration,
        maximum_antistate_bout_duration=maximum_antistate_bout_duration,
        frac=minimum_fraction_of_final_match,
    )
    full_hg.loc[is_nod & is_nodata, "state"] = "NoData"  # Restore NoData
    try:
        return matches[0].keep_states(["Wake"])
    except IndexError:
        warnings.warn(
            f"No extended wake period matching criteria found for {wne_subject.name} {experiment}"
        )
        return None


def get_conveyor_over_water_hypnogram(
    full_hg: hypnogram.FloatHypnogram,
    experiment: str,
    sglx_subject: wne.sglx.SGLXSubject,
) -> hypnogram.FloatHypnogram:
    (cow_start, cow_end) = get_conveyor_over_water_period(experiment, sglx_subject)
    return full_hg.trim(cow_start, cow_end)


def get_sleep_deprivation_hypnogram(
    full_hg: hypnogram.FloatHypnogram,
    experiment: str,
    wne_subject: wne.sglx.SGLXSubject,
) -> hypnogram.FloatHypnogram:
    sd_start, sd_end = get_sleep_deprivation_period(experiment, wne_subject)
    return full_hg.trim(sd_start, sd_end)


def compute_statistical_condition_hypnograms(
    lbrl_hg: hypnogram.FloatHypnogram,
    cons_hg: hypnogram.FloatHypnogram,
    experiment: str,
    sglx_subject: wne.sglx.SGLXSubject,
    extended_wake_kwargs: dict[str, float] = {},
    circadian_match_tolerance: float = pd.to_timedelta("0:30:00").total_seconds(),
) -> dict[str, hypnogram.FloatHypnogram]:
    """Compute hypnograms for different statistical conditions.

    Conditions consisting of Wake and/or NREM are 1 cumulative hour in length.
    Conditions consisting of REM are 10 cumulative minutes in length.

    Parameters
    ----------
    lbrl_hg : hypnogram.FloatHypnogram
        Full experiment hypnogram. "Liberal" because it provides the most accurate
        representation of the animal's sleep-wake state.
    cons_hg : hypnogram.FloatHypnogram
        Full experiment hypnogram. "Conservative" because additional artifactual
        periods have been marked.
    experiment : str
        Name of the experiment
    sglx_subject : wne.sglx.SGLXSubject
        The subject to compute hypnograms for.
    extended_wake_kwargs : dict[str, float]
        Keyword arguments to pass to `get_extended_wake_hypnogram`
    circadian_match_tolerance : float
        Tolerance for circadian match hypnogram, in seconds. Helpful in case there is
        not much sleep during the strict match window. Default is 30 minutes.

    Returns
    -------
    dict[str, hypnogram.FloatHypnogram]
        Dictionary mapping condition names to their corresponding hypnograms
    """
    _1h = pd.to_timedelta("1:00:00").total_seconds()
    _10min = pd.to_timedelta("0:10:00").total_seconds()

    hgs = dict()
    hgs["full_liberal"] = lbrl_hg
    hgs["full_conservative"] = cons_hg

    d1_hg = get_day1_hypnogram(cons_hg, experiment, sglx_subject)
    hgs["bsl_wake"] = d1_hg.keep_states(["Wake"])
    hgs["bsl_rem"] = d1_hg.keep_states(["REM"])

    d1lp_hg = get_day1_light_period_hypnogram(cons_hg, experiment, sglx_subject)
    hgs["early_bsl_nrem"] = d1lp_hg.keep_states(["NREM"]).keep_first(_1h)
    hgs["early_bsl_rem"] = d1lp_hg.keep_states(["REM"]).keep_first(_10min)

    d1dp_hg = get_day1_dark_period_hypnogram(cons_hg, experiment, sglx_subject)
    hgs["last_bsl_nrem"] = d1dp_hg.keep_states(["NREM"]).keep_last(_1h)
    hgs["last_bsl_rem"] = d1dp_hg.keep_states(["REM"]).keep_last(_10min)

    sd_hg = get_sleep_deprivation_hypnogram(cons_hg, experiment, sglx_subject)
    hgs["sd"] = sd_hg.keep_states(["Wake", "NREM"])
    hgs["early_sd"] = hgs["sd"].keep_first(_1h)
    hgs["late_sd"] = hgs["sd"].keep_last(_1h)
    # Analagous to early/late_ext.

    hgs["sd_wake"] = sd_hg.keep_states(["Wake"])
    hgs["early_sd_wake"] = hgs["sd_wake"].keep_first(_1h)
    hgs["late_sd_wake"] = hgs["sd_wake"].keep_last(_1h)
    # Analagous to early/late_ext_wake.

    if experiment in [Exps.NOD, Exps.CTN]:
        nod_hg = get_novel_objects_hypnogram(cons_hg, experiment, sglx_subject)
        hgs["nod"] = nod_hg.keep_states(["Wake", "NREM"])
        hgs["early_nod"] = hgs["nod"].keep_first(_1h)
        hgs["late_nod"] = hgs["nod"].keep_last(_1h)

        hgs["nod_wake"] = nod_hg.keep_states(["Wake"])
        hgs["early_nod_wake"] = hgs["nod_wake"].keep_first(_1h)
        hgs["late_nod_wake"] = hgs["nod_wake"].keep_last(_1h)

    if experiment in [Exps.COW, Exps.CTN]:
        cow_hg = get_conveyor_over_water_hypnogram(cons_hg, experiment, sglx_subject)
        hgs["cow"] = cow_hg.keep_states(["Wake", "NREM"])
        hgs["early_cow"] = hgs["cow"].keep_first(_1h)
        hgs["late_cow"] = hgs["cow"].keep_last(_1h)

        hgs["cow_wake"] = cow_hg.keep_states(["Wake"])
        hgs["early_cow_wake"] = hgs["cow_wake"].keep_first(_1h)
        hgs["late_cow_wake"] = hgs["cow_wake"].keep_last(_1h)

    if experiment == Exps.CTN:
        ctn_hg = sd_hg
        hgs["ctn"] = ctn_hg.keep_states(["Wake", "NREM"])
        hgs["early_ctn"] = hgs["ctn"].keep_first(_1h)
        hgs["late_ctn"] = hgs["ctn"].keep_last(_1h)

        hgs["ctn_wake"] = ctn_hg.keep_states(["Wake"])
        hgs["early_ctn_wake"] = hgs["ctn_wake"].keep_first(_1h)
        hgs["late_ctn_wake"] = hgs["ctn_wake"].keep_last(_1h)

    ext_hg = get_extended_wake_hypnogram(
        lbrl_hg, experiment, sglx_subject, **extended_wake_kwargs
    )
    if ext_hg is None:
        ext_hg = sd_hg
    else:
        ext_hg = cons_hg.trim(ext_hg["start_time"].min(), ext_hg["end_time"].max())
        hgs["ext"] = ext_hg.keep_states(["Wake", "NREM"])
        hgs["early_ext"] = hgs["ext"].keep_first(_1h)
        hgs["late_ext"] = hgs["ext"].keep_last(_1h)
        # Scoring may be so good that local sleep was marked as NREM.
        # If you want "mixed wake", early/late_ext will include these microsleeps.

        # If you want "pure wake", you can use "ext_wake" and company.
        hgs["ext_wake"] = ext_hg.keep_states(["Wake"])
        hgs["early_ext_wake"] = hgs["ext_wake"].keep_first(_1h)
        hgs["late_ext_wake"] = hgs["ext_wake"].keep_last(_1h)
        # If you want to mixed wake exactly matched to these times, use e.g.
        # matched_early_ext = hgs["ext"].keep_states(["Wake", "NREM"]).trim(
        #   hgs["early_ext_wake"]["start_time"].min(),
        #   hgs["early_ext_wake"]["end_time"].max()
        # )
        # Note that `matched_early_ext` will not be exactly 1h long, and will not be
        # exactly the same as `hgs["early_ext"]`! You have to decide what you want!

    pdd2lp_hg = get_post_deprivation_day2_light_period_hypnogram(
        cons_hg,
        experiment,
        sglx_subject,
        sleep_deprivation_end=ext_hg["end_time"].max(),
    )
    hgs["early_rec_nrem"] = pdd2lp_hg.keep_states(["NREM"]).keep_first(_1h)
    hgs["early_rec_rem"] = pdd2lp_hg.keep_states(["REM"]).keep_first(_10min)
    hgs["late_rec_nrem"] = pdd2lp_hg.keep_states(["NREM"]).keep_last(_1h)
    hgs["late_rec_rem"] = pdd2lp_hg.keep_states(["REM"]).keep_last(_10min)

    hgs["early_rec_nrem_match"] = get_circadian_match_hypnogram(
        cons_hg,
        start=hgs["early_rec_nrem"]["start_time"].min() - circadian_match_tolerance,
        end=hgs["early_rec_nrem"]["end_time"].max() + circadian_match_tolerance,
    ).keep_states(["NREM"])
    hgs["early_rec_rem_match"] = get_circadian_match_hypnogram(
        cons_hg,
        start=hgs["early_rec_rem"]["start_time"].min() - circadian_match_tolerance,
        end=hgs["early_rec_rem"]["end_time"].max() + circadian_match_tolerance,
    ).keep_states(["REM"])

    d2dp_hg = get_day2_dark_period_hypnogram(cons_hg, experiment, sglx_subject)
    hgs["last_rec_nrem"] = d2dp_hg.keep_states(["NREM"]).keep_last(_1h)
    hgs["last_rec_rem"] = d2dp_hg.keep_states(["REM"]).keep_last(_10min)

    return hgs

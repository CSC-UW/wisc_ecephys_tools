import itertools as it

import matplotlib.pyplot as plt
import pandas as pd

from ecephys import hypnogram
from ecephys import wne
import wisc_ecephys_tools as wet

NOD = "novel_objects_deprivation"
SHARED_PROJECT_NAME = "shared_s3"
PROJ = wet.get_wne_project(SHARED_PROJECT_NAME)


def get_novel_objects_period(
    experiment: str, subject: wne.sglx.SGLXSubject
) -> tuple[float, float]:
    params = PROJ.load_experiment_subject_params(experiment, subject.name)
    probe = params["hypnogram_probe"]

    start = pd.to_datetime(params["novel_objects_start"])
    start = subject.dt2t(experiment, probe, start)

    end = pd.to_datetime(params["novel_objects_end"])
    end = subject.dt2t(experiment, probe, end)

    return (start, end)


def get_novel_objects_hypnogram(
    experiment: str, subject: wne.sglx.SGLXSubject
) -> hypnogram.FloatHypnogram:
    hg = PROJ.load_float_hypnogram(experiment, subject.name)
    (nod_start, nod_end) = wet.shared.get_novel_objects_period(experiment, subject)
    return hg.trim(nod_start, nod_end)


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
    params = PROJ.load_experiment_subject_params(experiment, subject.name)
    on = pd.DataFrame(
        {"time": [pd.to_datetime(x) for x in params["lightsOn"]], "transition": "on"}
    )
    off = pd.DataFrame(
        {"time": [pd.to_datetime(x) for x in params["lightsOff"]], "transition": "off"}
    )
    df = pd.concat([on, off]).sort_values("time").reset_index(drop=True)
    if as_float:
        df["time"] = subject.dt2t(
            experiment, params["hypnogram_probe"], df["time"].values
        )

    periods = list(it.pairwise(df.itertuples()))
    intervals = [(start.time, end.time) for start, end in periods]
    labels = [start.transition for start, _ in periods]
    return intervals, labels


def plot_lights_overlay(
    intervals: list[tuple],
    interval_labels: list[str],
    ax: plt.Axes,
    ymin=0.98,
    ymax=1.0,
    alpha=1.0,
    colors={"on": "yellow", "off": "gray"},  # Keys are from interval_labels
):
    """Take intervals and labels, as returned by `get_light_dark_periods()`, and use these to overlay
    the light/dark cycle onto a plot."""
    xlim = ax.get_xlim()

    for (tOn, tOff), lbl in zip(intervals, interval_labels):
        ax.axvspan(
            tOn,
            tOff,
            alpha=alpha,
            color=colors[lbl],
            zorder=1000,
            ec="none",
            ymin=ymin,
            ymax=ymax,
        )

    ax.set_xlim(xlim)


def get_day1_hypnogram(
    experiment: str, subject: wne.sglx.SGLXSubject
) -> hypnogram.FloatHypnogram:
    hg = PROJ.load_float_hypnogram(experiment, subject.name)
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return hg.trim(
        intervals[0][0],  # start of first light period,
        intervals[1][1],  # end of first dark period
    )


def get_day2_hypnogram(
    experiment: str, subject: wne.sglx.SGLXSubject
) -> hypnogram.FloatHypnogram:
    hg = PROJ.load_float_hypnogram(experiment, subject.name)
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return hg.trim(
        intervals[2][0],  # start of first light period,
        intervals[3][1],  # end of first dark period
    )


def get_day1_light_period_hypnogram(
    experiment: str, subject: wne.sglx.SGLXSubject
) -> hypnogram.FloatHypnogram:
    hg = PROJ.load_float_hypnogram(experiment, subject.name)
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return hg.trim(
        intervals[0][0],  # start of first light period
        intervals[0][1],  # end of first light period
    )


def get_day1_dark_period_hypnogram(
    experiment: str, subject: wne.sglx.SGLXSubject
) -> hypnogram.FloatHypnogram:
    hg = PROJ.load_float_hypnogram(experiment, subject)
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return hg.trim(
        intervals[1][0],  # start of first dark period
        intervals[1][1],  # end of first dark period
    )


def get_day2_light_period_hypnogram(
    experiment: str, subject: wne.sglx.SGLXSubject
) -> hypnogram.FloatHypnogram:
    hg = PROJ.load_float_hypnogram(experiment, subject.name)
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return hg.trim(
        intervals[2][0],  # start of second light period
        intervals[2][1],  # end of second light period
    )


def get_post_deprivation_day2_light_period_hypnogram(
    experiment: str, subject: wne.sglx.SGLXSubject, sleep_deprivation_end: float
) -> hypnogram.FloatHypnogram:
    hg = get_day2_light_period_hypnogram(experiment, subject)
    return hg.trim(sleep_deprivation_end, hg["end_time"].max())


def get_circadian_match_hypnogram(
    experiment: str, subject: wne.sglx.SGLXSubject, start: float, end: float
) -> hypnogram.FloatHypnogram:
    hg = PROJ.load_float_hypnogram(experiment, subject.name)
    match_start = start - pd.to_timedelta("24h").total_seconds()
    match_end = end - pd.to_timedelta("24h").total_seconds()
    return hg.trim(match_start, match_end)


def compute_basic_novel_objects_deprivation_experiment_hypnograms(
    subject: wne.sglx.SGLXSubject, duration="1:00:00"
) -> dict[str, hypnogram.FloatHypnogram]:
    duration = pd.to_timedelta(duration).total_seconds()
    hgs = dict()

    nod_hg = get_novel_objects_hypnogram(NOD, subject)
    hgs["Early NOD"] = nod_hg.keep_first(duration)
    hgs["Late NOD"] = nod_hg.keep_last(duration)

    pdd2_hg = get_post_deprivation_day2_light_period_hypnogram(
        NOD, subject, nod_hg["end_time"].max()
    )
    rslp_hg = pdd2_hg.keep_states(["NREM"])
    hgs["Early Recovery NREM"] = rslp_hg.keep_first(duration)
    hgs["Late Recovery NREM"] = rslp_hg.keep_last(duration)

    match_hg = get_circadian_match_hypnogram(
        NOD,
        subject,
        hgs["Early Recovery NREM"]["start_time"].min(),
        hgs["Early Recovery NREM"]["end_time"].max(),
    ).keep_states(["NREM"])
    hgs["Early Recovery NREM match"] = match_hg

    hgs["Early Baseline NREM"] = (
        get_day1_light_period_hypnogram(NOD, subject)
        .keep_states(["NREM"])
        .keep_first(duration)
    )
    return hgs

import itertools as it

import matplotlib.pyplot as plt
from ecephys.wne.sglx.utils import load_reconciled_float_hypnogram
import pandas as pd

from ecephys import hypnogram
from ecephys import wne
import wisc_ecephys_tools as wet

NOD = "novel_objects_deprivation"
SHARED_PROJECT_NAME = "shared"
PROJ = wet.get_sglx_project(SHARED_PROJECT_NAME)


##################################
###### Experiment-specific #######
##################################


def get_light_dark_periods(experiment: str, subject: wne.sglx.SGLXSubject, as_float: bool = True):
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
    on = pd.DataFrame({"time": [pd.to_datetime(x) for x in params["lightsOn"]], "transition": "on"})
    off = pd.DataFrame({"time": [pd.to_datetime(x) for x in params["lightsOff"]], "transition": "off"})
    df = pd.concat([on, off]).sort_values("time").reset_index(drop=True)
    if as_float:
        df["time"] = subject.dt2t(experiment, params["hypnogram_probe"], df["time"].values)

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


def get_novel_objects_period(experiment: str, subject: wne.sglx.SGLXSubject) -> tuple[float, float]:
    params = PROJ.load_experiment_subject_params(experiment, subject.name)
    probe = params["hypnogram_probe"]

    start = pd.to_datetime(params["novel_objects_start"])
    start = subject.dt2t(experiment, probe, start)

    end = pd.to_datetime(params["novel_objects_end"])
    end = subject.dt2t(experiment, probe, end)

    return (start, end)


##################################
###### Analysis-specific #######
##################################


def get_full_reconciled_hypnogram(
    experiment: str, subject: wne.sglx.SGLXSubject, probes: list[str], sources: list[str]
) -> hypnogram.FloatHypnogram:
    """
    Load FloatHypnogram reconciled with LF/AP/sorting artifacts & NoData.

    Ensures that the probes' actual NoData bouts and artifacts are incorporated
    in the returned hypnogram.

    Parameters:
    ===========
    experiment: str
    subject: SGLXSubject
    probes: list[str]
        Probes for which we load bouts to reconcile with raw hypnogram
    sources: list[str]
        Sources must be one of ["ap", "lf", "sorting"].
        For "lf" and "ap" source, the NoData bouts are inferred from the sglx filetable,
        and the artifacts are loaded from the project's default consolidated
        artifact file.  For "sorting" source, NoData bouts are loaded from the
        sorting segments table.
    """
    return load_reconciled_float_hypnogram(
        PROJ,
        experiment,
        subject,
        probes,
        sources,
        simplify=True,
        alias="full",
        sorting="sorting",
    )


def get_novel_objects_hypnogram(
    full_hg: hypnogram.FloatHypnogram, experiment: str, subject: wne.sglx.SGLXSubject
) -> hypnogram.FloatHypnogram:
    (nod_start, nod_end) = wet.shared.get_novel_objects_period(experiment, subject)
    return full_hg.trim(nod_start, nod_end)


def get_day1_hypnogram(
    full_hg: hypnogram.FloatHypnogram, experiment: str, subject: wne.sglx.SGLXSubject
) -> hypnogram.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[0][0],  # start of first light period,
        intervals[1][1],  # end of first dark period
    )


def get_day2_hypnogram(
    full_hg: hypnogram.FloatHypnogram, experiment: str, subject: wne.sglx.SGLXSubject
) -> hypnogram.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[2][0],  # start of first light period,
        intervals[3][1],  # end of first dark period
    )


def get_day1_light_period_hypnogram(
    full_hg: hypnogram.FloatHypnogram, experiment: str, subject: wne.sglx.SGLXSubject
) -> hypnogram.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[0][0],  # start of first light period
        intervals[0][1],  # end of first light period
    )


def get_day1_dark_period_hypnogram(
    full_hg: hypnogram.FloatHypnogram, experiment: str, subject: wne.sglx.SGLXSubject
) -> hypnogram.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[1][0],  # start of first dark period
        intervals[1][1],  # end of first dark period
    )


def get_day2_light_period_hypnogram(
    full_hg: hypnogram.FloatHypnogram, experiment: str, subject: wne.sglx.SGLXSubject
) -> hypnogram.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[2][0],  # start of second light period
        intervals[2][1],  # end of second light period
    )


def get_day2_dark_period_hypnogram(
    full_hg: hypnogram.FloatHypnogram, experiment: str, subject: wne.sglx.SGLXSubject
) -> hypnogram.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[3][0],  # start of second dark period
        intervals[3][1],  # end of second dark period
    )


def get_post_deprivation_day2_light_period_hypnogram(
    full_hg: hypnogram.FloatHypnogram, experiment: str, subject: wne.sglx.SGLXSubject
) -> hypnogram.FloatHypnogram:
    hg = get_day2_light_period_hypnogram(full_hg, experiment, subject)
    nod_hg = get_novel_objects_hypnogram(full_hg, experiment, subject)
    sleep_deprivation_end = nod_hg.end_time.max()
    return hg.trim(sleep_deprivation_end, hg["end_time"].max())


def get_circadian_match_hypnogram(
    full_hg: hypnogram.FloatHypnogram, start: float, end: float
) -> hypnogram.FloatHypnogram:
    match_start = start - pd.to_timedelta("24h").total_seconds()
    match_end = end - pd.to_timedelta("24h").total_seconds()
    return full_hg.trim(match_start, match_end).keep_states(["NREM"])


def compute_basic_novel_objects_deprivation_experiment_hypnograms(
    subject: wne.sglx.SGLXSubject,
    probes: list[str],
    sources: list[str],
    duration="1:00:00",
) -> dict[str, hypnogram.FloatHypnogram]:
    """
    Load NOD FloatHypnograms reconciled with LF/AP/sorting artifacts & NoData.

    Ensures that the probes' actual NoData bouts and artifacts are incorporated
    in the returned hypnograms

    Parameters:
    ===========
    subject: SGLXSubject
    probes: list[str]
        Probes for which we load bouts to reconcile with raw hypnogram
    sources: list[str]
        Sources must be one of ["ap", "lf", "sorting"].
        For "lf" and "ap" source, the NoData bouts are inferred from the sglx filetable,
        and the artifacts are loaded from the project's default consolidated
        artifact file.  For "sorting" source, NoData bouts are loaded from the
        sorting segments table.
    """
    duration = pd.to_timedelta(duration).total_seconds()
    hgs = dict()

    full_hg = get_full_reconciled_hypnogram(NOD, subject, probes, sources)

    hgs["Full 48h"] = full_hg

    nod_hg = get_novel_objects_hypnogram(full_hg, NOD, subject).keep_states(["Wake"])
    hgs["Early NOD"] = nod_hg.keep_first(duration)
    hgs["Late NOD"] = nod_hg.keep_last(duration)

    pdd2_hg = get_post_deprivation_day2_light_period_hypnogram(full_hg, NOD, subject)
    rslp_hg = pdd2_hg.keep_states(["NREM"])
    hgs["Early Recovery NREM"] = rslp_hg.keep_first(duration)
    hgs["Late Recovery NREM"] = rslp_hg.keep_last(duration)

    match_hg = get_circadian_match_hypnogram(
        full_hg,
        NOD,
        subject,
        hgs["Early Recovery NREM"]["start_time"].min(),
        hgs["Early Recovery NREM"]["end_time"].max(),
    ).keep_states(["NREM"])
    hgs["Early Recovery NREM match"] = match_hg

    hgs["Early Baseline NREM"] = (
        get_day1_light_period_hypnogram(full_hg, NOD, subject).keep_states(["NREM"]).keep_first(duration)
    )
    return hgs

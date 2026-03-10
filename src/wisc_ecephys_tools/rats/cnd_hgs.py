"""
This module contains functions for getting hypnograms that cover different "conditions",
i.e. periods and states of interest. For example, the light/dark periods, the sleep
deprivation period, recovery NREM sleep, etc.

The `exp_hgs` module, on the other hand, contains functions for getting a total
experiment hypnogram, from which the hypnograms in this module are derived.

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
from pathlib import Path
from types import MappingProxyType
from typing import Final

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ecephys import hypnogram as hyp
from ecephys import plot as eplt
from ecephys import wne
from wisc_ecephys_tools import core
from wisc_ecephys_tools.rats.constants import SleepDeprivationExperiments as Exps

_LEGACY_CONDITION_NAMES_MAP: Final[MappingProxyType[str, str]] = MappingProxyType(
    {
        # Full experiment hypnograms
        "full_liberal": "Full.Liberal",
        "full_conservative": "Full.Conservative",
        # Baseline
        "bsl_wake": "BSL.Wake",
        "bsl_rem": "BSL.REM",
        "early_bsl_nrem": "Early.BSL.NREM",
        "early_bsl_rem": "Early.BSL.REM",
        "last_bsl_nrem": "Last.BSL.NREM",
        "last_bsl_rem": "Last.BSL.REM",
        # Sleep deprivation (mixed Wake+NREM)
        "sd": "SD",
        "early_sd": "Early.SD",
        "late_sd": "Late.SD",
        # Sleep deprivation (pure Wake)
        "sd_wake": "SD.Wake",
        "early_sd_wake": "Early.SD.Wake",
        "late_sd_wake": "Late.SD.Wake",
        # Novel objects deprivation (mixed Wake+NREM)
        "nod": "NOD",
        "early_nod": "Early.NOD",
        "late_nod": "Late.NOD",
        # Novel objects deprivation (pure Wake)
        "nod_wake": "NOD.Wake",
        "early_nod_wake": "Early.NOD.Wake",
        "late_nod_wake": "Late.NOD.Wake",
        # Conveyor over water (mixed Wake+NREM)
        "cow": "COW",
        "early_cow": "Early.COW",
        "late_cow": "Late.COW",
        # Conveyor over water (pure Wake)
        "cow_wake": "COW.Wake",
        "early_cow_wake": "Early.COW.Wake",
        "late_cow_wake": "Late.COW.Wake",
        # Conveyor then novelty (mixed Wake+NREM)
        "ctn": "CTN",
        "early_ctn": "Early.CTN",
        "late_ctn": "Late.CTN",
        # Conveyor then novelty (pure Wake)
        "ctn_wake": "CTN.Wake",
        "early_ctn_wake": "Early.CTN.Wake",
        "late_ctn_wake": "Late.CTN.Wake",
        # Extended wake (mixed Wake+NREM)
        "ext": "EXT",
        "early_ext": "Early.EXT",
        "late_ext": "Late.EXT",
        # Extended wake (pure Wake)
        "ext_wake": "EXT.Wake",
        "early_ext_wake": "Early.EXT.Wake",
        "late_ext_wake": "Late.EXT.Wake",
        # Recovery
        "early_rec_nrem": "Early.REC.NREM",
        "early_rec_rem": "Early.REC.REM",
        "late_rec_nrem": "Late.REC.NREM",
        "late_rec_rem": "Late.REC.REM",
        "last_rec_nrem": "Last.REC.NREM",
        "last_rec_rem": "Last.REC.REM",
        # Circadian match
        "early_rec_nrem_match": "Early.REC.NREM.Match",
        "early_rec_rem_match": "Early.REC.REM.Match",
    }
)


def get_light_dark_periods(
    experiment: str, subject: wne.sglx.SGLXSubject, as_float: bool = True
) -> tuple[list[tuple], list[str]]:
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
    full_hg: hyp.FloatHypnogram, experiment: str, subject: wne.sglx.SGLXSubject
) -> hyp.FloatHypnogram:
    (nod_start, nod_end) = get_novel_objects_period(experiment, subject)
    return full_hg.trim(nod_start, nod_end)


def get_day1_hypnogram(
    full_hg: hyp.FloatHypnogram,
    experiment: str,
    subject: wne.sglx.SGLXSubject,
) -> hyp.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[0][0],  # start of first light period,
        intervals[1][1],  # end of first dark period
    )


def get_day2_hypnogram(
    full_hg: hyp.FloatHypnogram,
    experiment: str,
    subject: wne.sglx.SGLXSubject,
) -> hyp.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[2][0],  # start of first light period,
        intervals[3][1],  # end of first dark period
    )


def get_day1_light_period_hypnogram(
    full_hg: hyp.FloatHypnogram,
    experiment: str,
    subject: wne.sglx.SGLXSubject,
) -> hyp.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[0][0],  # start of first light period
        intervals[0][1],  # end of first light period
    )


def get_day1_dark_period_hypnogram(
    full_hg: hyp.FloatHypnogram,
    experiment: str,
    subject: wne.sglx.SGLXSubject,
) -> hyp.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[1][0],  # start of first dark period
        intervals[1][1],  # end of first dark period
    )


def get_day2_light_period_hypnogram(
    full_hg: hyp.FloatHypnogram,
    experiment: str,
    subject: wne.sglx.SGLXSubject,
) -> hyp.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[2][0],  # start of second light period
        intervals[2][1],  # end of second light period
    )


def get_day2_dark_period_hypnogram(
    full_hg: hyp.FloatHypnogram,
    experiment: str,
    subject: wne.sglx.SGLXSubject,
) -> hyp.FloatHypnogram:
    intervals, labels = get_light_dark_periods(experiment, subject)
    assert labels == ["on", "off", "on", "off"]
    return full_hg.trim(
        intervals[3][0],  # start of second dark period
        intervals[3][1],  # end of second dark period
    )


def get_post_deprivation_day2_light_period_hypnogram(
    full_hg: hyp.FloatHypnogram,
    experiment: str,
    subject: wne.sglx.SGLXSubject,
    sleep_deprivation_end: float,  # This is a bit of a misnomer. It could also be the end of extended wake.
) -> hyp.FloatHypnogram:
    d2lp_hg = get_day2_light_period_hypnogram(full_hg, experiment, subject)
    return d2lp_hg.trim(sleep_deprivation_end, d2lp_hg["end_time"].max())


def get_circadian_match_hypnogram(
    full_hg: hyp.FloatHypnogram, start: float, end: float
) -> hyp.FloatHypnogram:
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
    elif experiment == Exps.COW:
        return get_conveyor_over_water_period(experiment, wne_subject)
    elif experiment == Exps.CTN:
        start = min(get_conveyor_over_water_period(experiment, wne_subject))
        end = max(get_novel_objects_period(experiment, wne_subject))
        return start, end
    else:
        raise ValueError(
            f"Experiment {experiment} does not have a sleep deprivation period."
        )


def get_extended_wake_hypnogram(
    full_hg: hyp.FloatHypnogram,
    experiment: str,
    wne_subject: wne.sglx.SGLXSubject,
    minimum_endpoint_bout_duration: float = 120,
    maximum_antistate_bout_duration: float = 90,
    minimum_fraction_of_final_match: float = 0.95,
) -> hyp.FloatHypnogram | None:
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
    full_hg: hyp.FloatHypnogram,
    experiment: str,
    sglx_subject: wne.sglx.SGLXSubject,
) -> hyp.FloatHypnogram:
    (cow_start, cow_end) = get_conveyor_over_water_period(experiment, sglx_subject)
    return full_hg.trim(cow_start, cow_end)


def get_sleep_deprivation_hypnogram(
    full_hg: hyp.FloatHypnogram,
    experiment: str,
    wne_subject: wne.sglx.SGLXSubject,
) -> hyp.FloatHypnogram:
    sd_start, sd_end = get_sleep_deprivation_period(experiment, wne_subject)
    return full_hg.trim(sd_start, sd_end)


def compute_statistical_condition_hypnograms(
    lbrl_hg: hyp.FloatHypnogram,
    cons_hg: hyp.FloatHypnogram,
    experiment: str,
    sglx_subject: wne.sglx.SGLXSubject,
    extended_wake_kwargs: dict[str, float] = {},
    circadian_match_tolerance: float = pd.to_timedelta("0:30:00").total_seconds(),
) -> dict[str, hyp.FloatHypnogram]:
    """Compute hypnograms for different statistical conditions.

    Conditions consisting of Wake and/or NREM are 1 cumulative hour in length.
    Conditions consisting of REM are 10 cumulative minutes in length.

    Parameters
    ----------
    lbrl_hg : hyp.FloatHypnogram
        Full experiment hypnogram. "Liberal" because it provides the most accurate
        representation of the animal's sleep-wake state.
    cons_hg : hyp.FloatHypnogram
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
    dict[str, hyp.FloatHypnogram]
        Dictionary mapping condition names to their corresponding hypnograms
    """
    _1h = pd.to_timedelta("1:00:00").total_seconds()
    _10min = pd.to_timedelta("0:10:00").total_seconds()

    hgs = dict()
    hgs["Full.Liberal"] = lbrl_hg
    hgs["Full.Conservative"] = cons_hg

    d1_hg = get_day1_hypnogram(cons_hg, experiment, sglx_subject)
    hgs["BSL.Wake"] = d1_hg.keep_states(["Wake"])
    hgs["BSL.REM"] = d1_hg.keep_states(["REM"])

    d1lp_hg = get_day1_light_period_hypnogram(cons_hg, experiment, sglx_subject)
    hgs["Early.BSL.NREM"] = d1lp_hg.keep_states(["NREM"]).keep_first(_1h)
    hgs["Early.BSL.REM"] = d1lp_hg.keep_states(["REM"]).keep_first(_10min)

    d1dp_hg = get_day1_dark_period_hypnogram(cons_hg, experiment, sglx_subject)
    hgs["Last.BSL.NREM"] = d1dp_hg.keep_states(["NREM"]).keep_last(_1h)
    hgs["Last.BSL.REM"] = d1dp_hg.keep_states(["REM"]).keep_last(_10min)

    sd_hg = get_sleep_deprivation_hypnogram(cons_hg, experiment, sglx_subject)
    hgs["SD"] = sd_hg.keep_states(["Wake", "NREM"])
    hgs["Early.SD"] = hgs["SD"].keep_first(_1h)
    hgs["Late.SD"] = hgs["SD"].keep_last(_1h)
    # Analogous to Early/Late.EXT.

    hgs["SD.Wake"] = sd_hg.keep_states(["Wake"])
    hgs["Early.SD.Wake"] = hgs["SD.Wake"].keep_first(_1h)
    hgs["Late.SD.Wake"] = hgs["SD.Wake"].keep_last(_1h)
    # Analogous to Early/Late.EXT.Wake.

    if experiment in [Exps.NOD, Exps.CTN]:
        nod_hg = get_novel_objects_hypnogram(cons_hg, experiment, sglx_subject)
        hgs["NOD"] = nod_hg.keep_states(["Wake", "NREM"])
        hgs["Early.NOD"] = hgs["NOD"].keep_first(_1h)
        hgs["Late.NOD"] = hgs["NOD"].keep_last(_1h)

        hgs["NOD.Wake"] = nod_hg.keep_states(["Wake"])
        hgs["Early.NOD.Wake"] = hgs["NOD.Wake"].keep_first(_1h)
        hgs["Late.NOD.Wake"] = hgs["NOD.Wake"].keep_last(_1h)

    if experiment in [Exps.COW, Exps.CTN]:
        cow_hg = get_conveyor_over_water_hypnogram(cons_hg, experiment, sglx_subject)
        hgs["COW"] = cow_hg.keep_states(["Wake", "NREM"])
        hgs["Early.COW"] = hgs["COW"].keep_first(_1h)
        hgs["Late.COW"] = hgs["COW"].keep_last(_1h)

        hgs["COW.Wake"] = cow_hg.keep_states(["Wake"])
        hgs["Early.COW.Wake"] = hgs["COW.Wake"].keep_first(_1h)
        hgs["Late.COW.Wake"] = hgs["COW.Wake"].keep_last(_1h)

    if experiment == Exps.CTN:
        ctn_hg = sd_hg
        hgs["CTN"] = ctn_hg.keep_states(["Wake", "NREM"])
        hgs["Early.CTN"] = hgs["CTN"].keep_first(_1h)
        hgs["Late.CTN"] = hgs["CTN"].keep_last(_1h)

        hgs["CTN.Wake"] = ctn_hg.keep_states(["Wake"])
        hgs["Early.CTN.Wake"] = hgs["CTN.Wake"].keep_first(_1h)
        hgs["Late.CTN.Wake"] = hgs["CTN.Wake"].keep_last(_1h)

    ext_hg = get_extended_wake_hypnogram(
        lbrl_hg, experiment, sglx_subject, **extended_wake_kwargs
    )
    if ext_hg is None:
        ext_hg = sd_hg
    else:
        ext_hg = cons_hg.trim(ext_hg["start_time"].min(), ext_hg["end_time"].max())
        hgs["EXT"] = ext_hg.keep_states(["Wake", "NREM"])
        hgs["Early.EXT"] = hgs["EXT"].keep_first(_1h)
        hgs["Late.EXT"] = hgs["EXT"].keep_last(_1h)
        # Scoring may be so good that local sleep was marked as NREM.
        # If you want "mixed wake", Early/Late.EXT will include these microsleeps.

        # If you want "pure wake", you can use "EXT.Wake" and company.
        hgs["EXT.Wake"] = ext_hg.keep_states(["Wake"])
        hgs["Early.EXT.Wake"] = hgs["EXT.Wake"].keep_first(_1h)
        hgs["Late.EXT.Wake"] = hgs["EXT.Wake"].keep_last(_1h)
        # If you want mixed wake exactly matched to these times, use e.g.
        # matched_early_ext = hgs["EXT"].keep_states(["Wake", "NREM"]).trim(
        #   hgs["Early.EXT.Wake"]["start_time"].min(),
        #   hgs["Early.EXT.Wake"]["end_time"].max()
        # )
        # Note that `matched_early_ext` will not be exactly 1h long, and will not be
        # exactly the same as `hgs["Early.EXT"]`! You have to decide what you want!

    # In rare cases, ext_hg["end_time"].max() can be < sd_hg["end_time"].max(), if
    # there was a lot of local sleep at the end of SD.
    earliest_recovery_start = max(ext_hg["end_time"].max(), sd_hg["end_time"].max())
    pdd2lp_hg = get_post_deprivation_day2_light_period_hypnogram(
        cons_hg,
        experiment,
        sglx_subject,
        sleep_deprivation_end=earliest_recovery_start,
    )
    hgs["Early.REC.NREM"] = pdd2lp_hg.keep_states(["NREM"]).keep_first(_1h)
    hgs["Early.REC.REM"] = pdd2lp_hg.keep_states(["REM"]).keep_first(_10min)
    hgs["Late.REC.NREM"] = pdd2lp_hg.keep_states(["NREM"]).keep_last(_1h)
    hgs["Late.REC.REM"] = pdd2lp_hg.keep_states(["REM"]).keep_last(_10min)

    hgs["Early.REC.NREM.Match"] = get_circadian_match_hypnogram(
        cons_hg,
        start=hgs["Early.REC.NREM"]["start_time"].min() - circadian_match_tolerance,
        end=hgs["Early.REC.NREM"]["end_time"].max() + circadian_match_tolerance,
    ).keep_states(["NREM"])
    hgs["Early.REC.REM.Match"] = get_circadian_match_hypnogram(
        cons_hg,
        start=hgs["Early.REC.REM"]["start_time"].min() - circadian_match_tolerance,
        end=hgs["Early.REC.REM"]["end_time"].max() + circadian_match_tolerance,
    ).keep_states(["REM"])

    d2dp_hg = get_day2_dark_period_hypnogram(cons_hg, experiment, sglx_subject)
    hgs["Last.REC.NREM"] = d2dp_hg.keep_states(["NREM"]).keep_last(_1h)
    hgs["Last.REC.REM"] = d2dp_hg.keep_states(["REM"]).keep_last(_10min)

    return hgs


def save_statistical_condition_hypnograms(
    hgs: dict[str, hyp.FloatHypnogram], path: str
) -> pd.DataFrame:
    """
    Save a dictionary of hypnograms, keyed by condition name, to a single parquet file
    that includes a column for the condition name.

    Returns the dataframe that was saved.
    """
    dfs = []
    for cond, hg in hgs.items():
        df = hg._df.copy()
        df["condition"] = cond
        dfs.append(df)
    out_df = pd.concat(dfs, ignore_index=True)
    out_df.to_parquet(path, index=False)
    return out_df


def load_statistical_condition_hypnograms(
    path: str | Path,
) -> dict[str, hyp.FloatHypnogram]:
    df = pd.read_parquet(path)
    # Translate legacy snake_case condition names to new Dot.PascalCase names.
    df["condition"] = df["condition"].replace(_LEGACY_CONDITION_NAMES_MAP)
    conditions = df["condition"].unique()
    hgs = {
        cond: hyp.FloatHypnogram(
            df[df["condition"] == cond]
            .drop(columns=["condition"])
            .reset_index(drop=True)
        )
        for cond in conditions
    }
    return hgs


def plot_condition_hgs_dense(
    hgs: dict[str, hyp.FloatHypnogram],
    palette: dict[str, str],
    experiment: str | None = None,
    subject: wne.sglx.SGLXSubject | None = None,
    show_ticklabels: bool = False,
) -> plt.Axes:
    """Plot each condition on the same axis, so that they can all be seen at once.

    Palette keys must be the names of the conditions to plot, and values must be
    matplotlib colors.

    If both experiment and subject are provided, the light periods will be plotted.
    """
    # Replace `state` with condition, so that we can use the `state_colors` argument to
    # `plot_hypnogram_overlay`.
    hgs = {k: v.copy() for k, v in hgs.items()}
    for condition in hgs.keys():
        hgs[condition]["state"] = condition

    # Reconcile conditions with a dummy that covers the whole experiment,
    # to ensure that the xlim is plotted correctly.
    df1 = pd.concat([hgs[c]._df for c in palette.keys() if c in hgs])
    df2 = hyp.FloatHypnogram.get_dummy(
        hgs["Full.Liberal"]["start_time"].min(),
        hgs["Full.Liberal"]["end_time"].max(),
    )._df
    df = hyp.reconcile_hypnograms(df1, df2)

    palette = palette.copy()
    palette["None"] = "white"
    ax = eplt.plot_hypnogram_overlay(
        df, xlim="hg", figsize=(16, 1), state_colors=palette
    )
    if experiment and subject:
        plot_lights_overlay(
            *get_light_dark_periods(experiment, subject),
            ax=ax,
            ymax=1.04,
        )
    if not show_ticklabels:
        ax.set_xticklabels([])
        ax.set_yticklabels([])
    return ax


def get_consensus(
    prb_hgs: dict[str, dict[str, hyp.FloatHypnogram]],
) -> tuple[dict[str, hyp.FloatHypnogram], pd.DataFrame]:
    """
    Get the consensus hypnogram for each condition, and a dataframe summarizing the
    duration of each condition in each probe.
    """
    # Get the set of conditions from each probe's hypnograms
    condition_lists = [list(hgs.keys()) for hgs in prb_hgs.values()]
    conditions = condition_lists[0]

    # Assert that all probes have the same conditions
    for cl in condition_lists[1:]:
        assert set(cl) == set(conditions), (
            "All probes must have the same set of conditions"
        )

    # Get the consensus hypnogram for each condition
    consensus_hgs = {
        condition: hyp.FloatHypnogram.get_consensus(
            *[prb_hgs[prb][condition] for prb in prb_hgs.keys()]
        ).drop_states(["None"])
        for condition in conditions
    }

    # Get the duration of each condition in each probe
    prb_durations = {
        prb: {
            condition: prb_hgs[prb][condition]["duration"].sum()
            for condition in conditions
        }
        for prb in prb_hgs.keys()
    }

    # Get the duration of each condition in the consensus hypnogram
    consensus_durations = {
        condition: consensus_hgs[condition]["duration"].sum()
        for condition in conditions
    }

    # Create a dataframe with both consensus and probe durations
    df = pd.DataFrame(
        {
            "condition": conditions,
            "consensus": list(consensus_durations.values()),
            **{prb: list(prb_durations[prb].values()) for prb in prb_hgs.keys()},
        }
    )

    # Calculate the approximate loss in duration for each condition
    df["approximate_loss"] = np.round(
        df[list(prb_hgs.keys())].min(axis=1) - df["consensus"], decimals=1
    )

    return consensus_hgs, df

import itertools
from typing import Callable

import pandas as pd

from ecephys import hypnogram as hyp
from ecephys import wne
from ecephys.wne.sglx import SGLXProject, SGLXSubject

from . import constants


def _load_ephyviewer_hypnogram_edits(
    project: wne.Project,
    experiment: str,
    subject: str,
    simplify: bool = True,
) -> hyp.FloatHypnogram:
    """
    Load a hypnogram of EphyViewer edits.

    Args:
        project: The project where the edits are stored.
        experiment: The experiment to load the edits for.
        subject: The subject to load the edits for.
        simplify: Whether to simplify the edit states.

    Returns:
        A hypnogram of EphyViewer edits. Empty if the file does not exist.
    """
    f = project.get_experiment_subject_file(
        experiment, subject, constants.Files.HYPNOGRAM_EPHYVIEWER_EDITS
    )
    if not f.exists():
        return hyp.FloatHypnogram(
            pd.DataFrame([], columns=["state", "start_time", "end_time", "duration"])
        )

    df = pd.read_csv(f, sep=",")
    df = df.rename({"time": "start_time", "label": "state"}, axis=1)
    df["end_time"] = df["start_time"] + df["duration"]
    hg = hyp.FloatHypnogram(df)
    if simplify:
        hg = hg.replace_states(wne.SIMPLIFIED_STATES)
    return hyp.FloatHypnogram(hyp.condense(hg._df, 0.1))


# TODO: This function needs to be differentiated from load_sglx_inclusions_and_artifacts.
# When would you use this one, and when would you use the other?
# It seems like this one should be used when a sorting already exists, whereas the other
# is used to create a sorting.
# TODO: This function does NOT actually return inclusions and artifacts separately.
# Why both with the second dummy return? Really all we are doing is loading the segments
# table, concerting to times, and then filtering to keep only the segments of type "keep".
# TODO: This probably does not need to be a function at all.
def _load_sorting_inclusions_and_artifacts(
    t2t: Callable,
    project: SGLXProject,
    sglx_subject: SGLXSubject,
    experiment: str,
    probe: str,
    alias: str,
    sorting: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Query inclusions from segments used in actual sorting
    # segments are in probe timebase and need to be converted to common timebase
    segments = wne.sglx.siutils.load_segments_table_from_sorting(
        project,
        sglx_subject.name,
        experiment,
        alias,
        probe,
        sorting,
        return_all_segment_types=True,
    ).copy()
    segments = pd.DataFrame(
        {
            "start_time": t2t(segments["segmentExpmtPrbAcqFirstTime"]),
            "end_time": t2t(segments["segmentExpmtPrbAcqLastTime"]),
            "type": segments["type"],
        }
    )  # Raw segment table is in probe timebase

    inclusions = segments.loc[segments["type"] == "keep"]
    artifacts = inclusions.iloc[:0].copy()  # Dummy

    return inclusions, artifacts


# TODO: This function needs to be differentiated from load_sorting_inclusions_and_artifacts.
# When would you use this one, and when would you use the other?
# Maybe load_probe_stream_inclusions_and_artifacts would be a better name?
def _load_sglx_inclusions_and_artifacts(
    t2t: Callable,
    project: SGLXProject,
    sglx_subject: SGLXSubject,
    experiment: str,
    probe: str,
    alias: str,
    stream: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if alias != "full":
        raise NotImplementedError("Restrict artifacts to alias")

    # Inclusions are available SGLX files
    # Need conversion from probetimebase
    ftable = sglx_subject.get_experiment_frame(
        experiment,
        alias,
        probe=probe,
        stream=stream,
        ftype="bin",
    )
    inclusions = pd.DataFrame(
        {
            "start_time": t2t(ftable["expmtPrbAcqFirstTime"]),
            "end_time": t2t(ftable["expmtPrbAcqLastTime"]),
        }
    )

    # Incorporate project-wide artifacts
    # Those are already in common-time base, no need for conversion
    artifacts = wne.utils.load_consolidated_artifacts(
        project, experiment, sglx_subject.name, probe, stream, simplify=True
    )

    return inclusions, artifacts


def _get_gaps(
    df: pd.DataFrame,
    t1_colname: str = "start_time",
    t2_colname: str = "end_time",
    min_gap_duration_sec: float = 0,
):
    gaps = pd.DataFrame(
        {
            t1_colname: df.iloc[:-1][t2_colname].values,
            t2_colname: df.iloc[1:][t1_colname].values,
        }
    )
    gaps["duration"] = gaps[t2_colname] - gaps[t1_colname]
    return gaps[gaps["duration"] > min_gap_duration_sec]


# TODO: This function's name does not appear to describe what it does: return all the NoData and/or artifactual periods from a probe.
def _load_bouts_to_reconcile_as_hypnogram(
    project: SGLXProject,
    experiment: str,
    sglx_subject: SGLXSubject,
    probe: str,
    source: str,  # TODO: Currently, you have to check first if the source exists. This function should probably do that for you.
    alias: str = "full",
    sorting: str = "sorting",
    min_bout_duration_sec: float = 0.1,
) -> hyp.FloatHypnogram:
    if source in ["sorting", "ap"]:
        stream = "ap"
    elif source == "lf":
        stream = "lf"
    else:
        raise ValueError(f"Invalid source: {source}")

    # Convert from probe timebase to common timebase asap
    t2t = wne.sglx.utils.get_time_synchronizer(
        project,
        sglx_subject,
        experiment,
        probe=probe,
        stream=stream,
    )

    if source == "sorting":
        inclusions, artifacts = _load_sorting_inclusions_and_artifacts(
            t2t,
            project,
            sglx_subject,
            experiment,
            probe,
            alias,
            sorting,
        )

    elif source in ["lf", "ap"]:
        inclusions, artifacts = _load_sglx_inclusions_and_artifacts(
            t2t,
            project,
            sglx_subject,
            experiment,
            probe,
            alias,
            stream,
        )

    # Infer "NoData" hypnogram from inclusions
    # 1-sample imprecision
    no_data = _get_gaps(
        inclusions,
        t1_colname="start_time",
        t2_colname="end_time",
    )
    no_data["state"] = "NoData"
    no_data_hg = hyp.FloatHypnogram(no_data)

    # Get "artifacts" hypnogram: "type" column now becomes "state"
    artifacts = artifacts.rename(columns={"type": "state"})
    artifacts["duration"] = artifacts["end_time"] - artifacts["start_time"]
    artifacts_hg = hyp.FloatHypnogram(artifacts)

    # Reconcile NoData & artifacts
    return hyp.FloatHypnogram(
        no_data_hg.reconcile(artifacts_hg, how="other")
        .keep_longer(min_bout_duration_sec)
        .reset_index(drop=True)
    )


# TODO: Retire this in favor of wne.utils.load_consolidated_hypnogram().
def _load_consolidated_hypnogram(
    project: wne.Project,
    experiment: str,
    subject: str,
    simplify: bool = True,
) -> hyp.FloatHypnogram:
    """Load FloatHypnogram from consolidated hypnogram.htsv project file.

    Important: This hypnogram might not be adequate for all use, as it does
    not necessarily account some excluded, missing or artifactual data
    from LF-band artifacts, AP-band artifacts, or sorting exclusions.  Consider
    using wisc_ecephys_tools.scoring.load_hypnogram instead.
    """
    f = project.get_experiment_subject_file(experiment, subject, wne.Files.HYPNOGRAM)
    hg = hyp.FloatHypnogram.from_htsv(f)
    if simplify:
        hg = hg.replace_states(wne.SIMPLIFIED_STATES)
        # TODO: This clean() should not be necessary. It is already done in ecephys.wne.sglx.pipeline.consoldate_visbrain_hypnograms.do_experiment_probe().
        # Although, it will change NaNs to NoData. Is that expected downstream somewhere?
        hg = hyp.FloatHypnogram.clean(hg._df)
    return hg


# TODO: There does need to be a function somewhere in wne that reconciles a consoldiated
# visbrain hypnogram with consolidated artifacts.
# TODO: The sources argument dictates the sources of the NoData and artifacts.
# The current options are "sorting", "ap", and "lf", but are misleading and ambiguous.
# For example, "lf" will pull NoData from the SGLX filetable for each specified probe,
# and artifacts from the project's consoldiated artifact files for each specified probe.
# So these are really separate sources.
# TODO: "sorting" is unable to distinguish between NoData and artifacts, because
# it is not possible to tell from the sorting segments table whether a segment was
# NoData or artifactual, I think? And so artifactual periods will be labled as nodata.
# One result of this is that the order of `sources` actually matters, because the last
# source can determine if a period is marked as NoData or artifactual.
# TODO: What if "sorting" is specified, but not all probes have a sorting?
# Or, what if an artifact file is not found for a probe-stream combination?
# TODO:
# Maybe:
# - `include_lf_sglx_filetable_nodata=True`
# - `include_lf_consolidated_artifacts=True`
# - `include_ap_sglx_filetable_nodata=True`
# - `include_ap_consolidated_artifacts=True`
# - `include_sorting_nodata=True`
# - `include_ephyviewer_edits=True`
def load_hypnogram(
    project: SGLXProject,
    experiment: str,
    subject: SGLXSubject,
    probes: list[str],
    sources: list[str],  #
    reconcile_ephyviewer_edits: bool = True,  # TODO: Why is this optional, when it is literally in the function's name?
    simplify: bool = True,
    alias="full",
    sorting="sorting",
) -> hyp.FloatHypnogram:
    """Load FloatHypnogram reconciled with LF/AP/sorting artifacts & NoData.

    Favor using this function, rather than load_raw_float_hypnogram, for
    actual analyses! It ensures that :
        - the probes' actual NoData bouts and # TODO: Actual as opposed to...? Where does the alleged discrepancy come from?
        - the probes' artifacts
        - Manual edits made post-hoc in ephyviewer
    are incorporated

    This is not guaranteed to be the case with the load_raw_float_hypnogram,
    in particular since:
        - SGLX files and artifacts may vary across streams/probes
        - Some bouts may have been excluded from a sorting # TODO: Why?

    If probes and sources are not passed (e.g. empty lists), this function effectively
    is just for loading the ephyviewer edits and/or cleaning.

    Parameters:
    ===========
    project: Project
        The project containing all the hypnogram, artifact, and nodata sources.
        Loading these piecemeal from separate projects is not supported.
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
        # TODO: How are these related? Is the sorting segments table always a superset of the consolidated artifact file?
    simplify: bool
        Passed to load_raw_float_hypnogram. Simplifies states from raw float hypnogram
    alias: str
        Alias used for sorting. Used only when querying "sorting" source.
    sorting: str
        Name of sorting. Used only when querying "sorting" source
    """
    SOURCES = ["sorting", "ap", "lf"]
    if not set(sources) <= set(SOURCES):
        raise ValueError(
            f"Invalid value in `sources` argument. The following sources are recognized: `{SOURCES}`"
        )  # TODO: This is not true. As written, sources=[] will also pass this test. Is that intended, or a bug?
    hg = _load_consolidated_hypnogram(
        project,
        experiment,
        subject.name,
        simplify=simplify,
    )
    if reconcile_ephyviewer_edits:
        hg = hg.reconcile(
            _load_ephyviewer_hypnogram_edits(
                project, experiment, subject.name, simplify=simplify
            ),
            how="other",
        )

    # Only keep bouts that are artifact-free and have data on EVERY probe. The "most conservative" hypnogram, if you will.
    # Any period covered by this hypnogram is guaranteed to be artifact-free and have data on every probe.
    # SUS: If either sources or probes is an empty list, this for-loop will be bypassed entirely. Is that intended?
    # Almost certainly not. Both sources and probes should be required non-empty.
    for source, probe in itertools.product(sources, probes):
        hg = hg.reconcile(
            _load_bouts_to_reconcile_as_hypnogram(
                project,
                experiment,
                subject,
                probe,
                source,
                alias=alias,
                sorting=sorting,
            ),
            how="other",
        )

    return hyp.FloatHypnogram.clean(hg.reset_index(drop=True))

import pandas as pd

from ecephys import hypnogram as hyp
from ecephys import wne
from ecephys.wne.sglx import SGLXProject, SGLXSubject
from wisc_ecephys_tools import constants


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


def _get_gaps(
    df: pd.DataFrame,
    t1_colname: str = "start_time",
    t2_colname: str = "end_time",
    min_gap_duration_sec: float = 0,
) -> pd.DataFrame:
    gaps = pd.DataFrame(
        {
            t1_colname: df.iloc[:-1][t2_colname].values,
            t2_colname: df.iloc[1:][t1_colname].values,
        }
    )
    gaps["duration"] = gaps[t2_colname] - gaps[t1_colname]
    return gaps[gaps["duration"] > min_gap_duration_sec]


def _infer_nodata(has_data: pd.DataFrame) -> pd.DataFrame:
    no_data = _get_gaps(has_data)  # 1-sample imprecision
    no_data["state"] = "NoData"
    return no_data


def _get_nodata_from_sorting(
    project: SGLXProject,
    subject: SGLXSubject,
    experiment: str,
    probe: str,
) -> hyp.FloatHypnogram:
    """
    Get a hypnogram of NoData periods inferred from the sorting segments table.
    This is not entirely accurate, because segments may have been excluded from the
    sorting for reasons other than missing data.
    """
    segments = wne.sglx.siutils.load_segments_table_from_sorting(
        project,
        subject.name,
        experiment,
        "full",
        probe,
        "sorting",
        return_all_segment_types=True,
    ).copy()

    # Convert from probe timebase to common timebase asap
    t2t = wne.sglx.utils.get_time_synchronizer(
        project, subject, experiment, probe=probe, stream="ap"
    )
    segments = pd.DataFrame(
        {
            "start_time": t2t(segments["segmentExpmtPrbAcqFirstTime"]),
            "end_time": t2t(segments["segmentExpmtPrbAcqLastTime"]),
            "type": segments["type"],
        }
    )
    has_data = segments.loc[segments["type"] == "keep"]

    no_data = _infer_nodata(has_data)
    return hyp.FloatHypnogram(no_data)


def _get_nodata_from_sglx_filetable(
    project: SGLXProject, experiment: str, subject: SGLXSubject, probe: str, stream: str
) -> hyp.FloatHypnogram:
    """
    Get a hypnogram of NoData periods inferred from the SGLX filetable.
    """
    ftable = subject.get_experiment_frame(
        experiment,
        alias="full",
        probe=probe,
        stream=stream,
        ftype="bin",
    )

    # Convert from probe timebase to common timebase asap
    t2t = wne.sglx.utils.get_time_synchronizer(
        project,
        subject,
        experiment,
        probe=probe,
        stream=stream,
    )
    has_data = pd.DataFrame(
        {
            "start_time": t2t(ftable["expmtPrbAcqFirstTime"]),
            "end_time": t2t(ftable["expmtPrbAcqLastTime"]),
        }
    )

    no_data = _infer_nodata(has_data)
    return hyp.FloatHypnogram(no_data)


def _artifacts_as_hypnogram(artifacts: pd.DataFrame) -> hyp.FloatHypnogram:
    artifacts = artifacts.rename(columns={"type": "state"})
    artifacts["duration"] = artifacts["end_time"] - artifacts["start_time"]
    return hyp.FloatHypnogram(artifacts)


# We may want a function that reconciles the output of this one for multiple probes.
def load_hypnogram(
    project: SGLXProject,
    experiment: str,
    subject: SGLXSubject,
    probe: str,
    include_ephyviewer_edits: bool = True,
    include_sorting_nodata: bool = True,
    include_lf_consolidated_artifacts: bool = True,
    include_ap_consolidated_artifacts: bool = True,
    include_lf_sglx_filetable_nodata: bool = True,
    include_ap_sglx_filetable_nodata: bool = True,
    simplify: bool = True,
) -> hyp.FloatHypnogram:
    """Load a FloatHypnogram reconciled with EphyViewer edits, LF/AP/sorting artifacts,
     and NoData periods marked.

    Favor using this function, rather than ecephys.wne.utils.load_consolidated_hypnogram.

    Note that:
        - EphyViewer edits are probe-agnostic.
        - SGLX files and artifacts may vary across streams/probes
        - Some bouts may have been excluded from a sorting, that are not present in a
          probe's consolidated artifact file. However, I (GF) do not believe there is a
          guarantee that the exclusions derived from a sorting segments table are a
          superset of the exclusions derived from a probe's consolidated artifact file.
          This is because the consolidated artifacts table may be updated after a
          sorting is complete, and the sorting may not be re-done if the artifacts do
          not affect the AP band.
        - Some bouts may be marked as NoData in the SGLX filetable, but not in the
          consolidated artifact file.
        - The order of operations here does matter if any of the sources (apart from the
          consolidated hypnogram) disagree with each other!
          - We do ephyviewer edits first, so that they can't accidentally override
            other sources.
          - We do sorting NoData before LF/AP consolidated artifacts, because the
            sorting NoData actually includes some artifactual periods.
          - We do LF/AP consolidated artifacts next, to correct the sorting NoData.
            AP follows LF, because AP has the most temporal precision.
          - We do LF/AP SGLX filetable NoData last to resolve submillisecond
            conflicts between timestamps marked as both NoData and Artifact, erring
            on the side of NoData.

    Parameters:
    ===========
    project: ecephys.wne.SGLXProject
        The project containing all the hypnogram, artifact, and nodata sources.
        Loading these piecemeal from separate projects is not yet supported.
    experiment: str
    subject: SGLXSubject
    probe: str
        This probe's consolidated hypnogram, artifact files, and sorting segments table
        will be loaded.
    include_ephyviewer_edits: bool
        Whether to include EphyViewer edits. These are probe-agnostic.
    include_sorting_nodata: bool
        Whether to include NoData & artifact periods from the sorting segments table.
        Currently marks artifacts as NoData, but most or all of these mislabels will be
        corrected if e.g. `include_lf_consolidated_artifacts` is `True`.
        Assumes the sorting name is "sorting" and the alias is "full".
    include_lf_consolidated_artifacts: bool
        Whether to include artifact periods from the LF consolidated artifact file
    include_ap_consolidated_artifacts: bool
        Whether to include artifact periods from the AP consolidated artifact file
    include_lf_sglx_filetable_nodata: bool
        Whether to include NoData periods from the LF SGLX filetable
    include_ap_sglx_filetable_nodata: bool
        Whether to include NoData periods from the AP SGLX filetable
    simplify: bool
        If true, simplifes the consolidated hypnogram immeidately upon loading, before
        any reconcilition with artifacts, nodata, or ephyviewer edits is attempted. Also
        determines whether ephyviewer edits will be simplified upon loading.
    """
    hg = wne.utils.load_consolidated_hypnogram(
        project, experiment, subject.name, probe, simplify=simplify
    )

    # Reconcile ephyviewer edits first, so that they can't accidentally override
    # any artifact/nodata sources.
    if include_ephyviewer_edits:
        edits = _load_ephyviewer_hypnogram_edits(
            project, experiment, subject.name, simplify=simplify
        )
        hg = hg.reconcile(edits, how="other")

    if include_sorting_nodata:
        nodata = _get_nodata_from_sorting(project, subject, experiment, probe)
        hg = hg.reconcile(nodata, how="other")

    if include_lf_consolidated_artifacts:
        artifacts = wne.sglx.utils.load_consolidated_artifacts(
            project, experiment, subject.name, probe, "lf", simplify=True
        )
        hg = hg.reconcile(_artifacts_as_hypnogram(artifacts), how="other")

    if include_ap_consolidated_artifacts:
        artifacts = wne.sglx.utils.load_consolidated_artifacts(
            project, experiment, subject.name, probe, "ap", simplify=True
        )
        hg = hg.reconcile(_artifacts_as_hypnogram(artifacts), how="other")

    if include_lf_sglx_filetable_nodata:
        nodata = _get_nodata_from_sglx_filetable(
            project, experiment, subject, probe, "lf"
        )
        hg = hg.reconcile(nodata, how="other")

    if include_ap_sglx_filetable_nodata:
        nodata = _get_nodata_from_sglx_filetable(
            project, experiment, subject, probe, "ap"
        )
        hg = hg.reconcile(nodata, how="other")

    return hyp.FloatHypnogram.clean(hg.reset_index(drop=True))

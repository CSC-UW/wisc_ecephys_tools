import argparse

import numpy as np
import pandas as pd

import ecephys.deprecated.spindles.mua as mu_spindles
import wisc_ecephys_tools as wet
from ecephys.wne.sglx.utils import load_singleprobe_sorting
from ecephys.wne.siutils import get_quality_metric_filters

# Parse experiment, alias, subjectName, probe from command line
example_text = """
example:

python run_mu_spindles_detection.py experiment alias seahorse CNPIX4-Doppio,imec0,Po
"""
parser = argparse.ArgumentParser(
    description=("Run spindle detection from multi-unit activity."),
    epilog=example_text,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument("experiment", type=str, help="Name of experiment we run off for.")
parser.add_argument("alias", type=str, help="Name of alias we run off for.")
parser.add_argument("saveProject", type=str, help="Name of project we save in.")
parser.add_argument(
    "subject_probe_structure",
    type=str,
    help="Target structure. Comma-separated string of the form `'<subjectName>,<probe>,<structure>'",
)
args = parser.parse_args()

experiment = args.experiment
alias = args.alias
saveProjectName = args.saveProject
subjectName, probe, structure = args.subject_probe_structure.split(",")


def main():
    subject = wet.get_sglx_subject(subjectName)
    project = wet.get_sglx_project("shared_s3")
    saveProject = wet.get_sglx_project(saveProjectName)

    MULTI_UNIT_FILTERS = get_quality_metric_filters(
        "permissive",
        isolation_threshold=None,
        false_negatives_threshold=None,
        presence_threshold=None,
    )

    hg = project.load_float_hypnogram(experiment, subject.name, simplify=True)

    sorting = (
        load_singleprobe_sorting(
            project,
            subject,
            experiment,
            probe,
        )
        .refine_clusters(*MULTI_UNIT_FILTERS)
        .select_structures([structure])
    )

    mu_spiketrain_sec = sorting.get_trains_by_property(
        property_name="acronym", values=[structure], return_times=True
    )[structure]  # Merge unit trains within whole structure

    params = mu_spindles.get_mu_spindle_detection_params()

    # t_start, t_stop = 110000, 140000
    # hg = hg.keep_between_time(t_start, t_stop)
    # mu_spiketrain_sec = mu_spiketrain_sec[
    #     np.searchsorted(mu_spiketrain_sec, hg.start_time.min()) :
    #     np.searchsorted(mu_spiketrain_sec, hg.end_time.max())
    # ]

    try:
        (
            mu_sigma,
            mu,
            rpow,
            rpow_thresh,
            mrms,
            mrms_thresh,
            decision_function,
            spindles,
            troughs,
        ) = mu_spindles.detect_mu_spindles_from_spiketrain(
            mu_spiketrain_sec,
            params,
            hg=hg,
            artifacts=pd.DataFrame(),
        )
        spindles["Structure"] = structure
    except TypeError:  # N=0 finds. TODO
        import warnings

        warnings.warn("N=0 spindles. saving nothing.")
        return

    for state in hg.state.unique():
        print(
            f"{state} spindle rate: {(spindles['Stage'] == state).sum() / hg.keep_states([state]).duration.sum()} Hz"
        )

    spin_fpath = saveProject.get_experiment_subject_file(
        experiment, subject.name, f"{probe}.{structure}.mu_spindles.pqt"
    )
    troughs_fpath = saveProject.get_experiment_subject_file(
        experiment, subject.name, f"{probe}.{structure}.mu_spindle_troughs"
    )
    print(f"Save spindles: {spin_fpath}")
    print(f"Save troughs: {troughs_fpath}")
    spindles.to_parquet(spin_fpath)
    np.save(troughs_fpath, troughs, allow_pickle=True)


if __name__ == "__main__":
    main()

import argparse
import pickle

import numpy as np
import on_off_detection

import wisc_ecephys_tools as wet

# Parse experiment, alias, subjectName, probe from command line
example_text = """
example:

python run_spatial_off_detection.py experiment CNPIX4-Doppio,imec0,M2
"""
parser = argparse.ArgumentParser(
    description=("Run spatial off detection."),
    epilog=example_text,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument("experiment", type=str, help="Name of experiment we run off for.")
parser.add_argument(
    "pooled_states",
    type=str,
    help="Target states. Pooled together eg `NREM` or `N1,N2,NREM`",
)
parser.add_argument(
    "subject_probe_structure",
    type=str,
    help="Target structure. Comma-separated string of the form `'<subjectName>,<probe>,<struct>'",
)
parser.add_argument(
    "--n_jobs",
    required=False,
    type=int,
    default=10,
    help="Acronym of atlas structure (eg 'Cx') restricting the returned structures",
)
args = parser.parse_args()

experiment = args.experiment
subjectName, probe, structure = args.subject_probe_structure.split(",")
pooled_states = args.pooled_states.split(",")

# Data
filters = {
    "quality": {"good", "mua", "unsorted"},
}
# Exclude noise

min_unit_sumFR = 100  # Pass structures with fr below this

# Output Path
outputProjectName = "offs"

on_off_method = "hmmem"
on_off_params = {
    "binsize": 0.010,  # (s) (Discrete algorithm)
    "history_window_nbins": 10,  # Size of history window IN BINS
    "n_iter_EM": 200,  # Number of iterations for EM
    "n_iter_newton_ralphson": 100,
    "init_A": np.array(
        [[0.1, 0.9], [0.01, 0.99]]
    ),  # Initial transition probability matrix
    "init_state_off_on_fr_ratio_thresh": 0.05,  # During initialization, after removing OFFs shorter than 0.05msec, we remove OFFs with FR less than init_state_off_on_fr_ratio_thresh times the grand mean ON state firing rate
    "init_mu": None,  # ~ OFF rate. Fitted to data if None
    "init_alphaa": None,  # ~ difference between ON and OFF rate. Fitted to data if None
    "init_betaa": None,  # ~ Weight of recent history firing rate. Fitted to data if None,
    "min_off_duration": None,  # Merge active states separated by less than this
}

spatial_params = {
    # Windowing/pooling
    "window_min_size": 150,  # (um) Smallest allowed window size
    "window_min_fr": 100,  # (Hz) Smallest allowed within window population rate
    "window_fr_overlap": 0.75,  # (no unit) Population firing rate overlap between successive window
    # Merging of OFF states across windows
    "min_window_off_duration": 0.03,  # Remove OFFs shorter than this before merging
    "nearby_off_max_time_diff": 3,  # (sec)
    "min_shared_duration_overlap": 0.02,  # (sec)
    "min_depth_overlap": 50,  # (um)
}

###


def main():
    sglxSubject = wet.get_sglx_subject(subjectName)
    sglxProject = wet.get_sglx_project("shared")

    sorting = (
        ecephys.wne.sglx.siutils.load_singleprobe_sorting(
            sglxProject,
            sglxSubject,
            experiment,
            probe,
        )
        .refine_clusters(
            filters,
            include_nans=True,
            verbose=False,
        )
        .select_structures([structure])
    )

    hg = wet.rats.scoring.load_hypnogram(
        sglxProject,
        experiment,
        sglxSubject,
        [probe],
        ["sorting"],
        reconcile_ephyviewer_edits=True,
        simplify=True,
    ).keep_states(pooled_states)

    properties = sorting.properties
    all_trains = sorting.get_cluster_trains(
        return_times=True,
        start_time=hg.start_time.min(),
        end_time=hg.end_time.max(),
    )
    trains = [all_trains[row.cluster_id] for row in properties.itertuples()]
    cluster_ids = [row.cluster_id for row in properties.itertuples()]
    depths = [row.depth for row in properties.itertuples()]

    model = on_off_detection.SpatialOffModel(
        trains,
        depths,
        hg._df,
        cluster_ids=cluster_ids,
        on_off_method=on_off_method,
        on_off_params=on_off_params,
        spatial_params=spatial_params,
        n_jobs=args.n_jobs,
    )

    if np.sum(model.get_cluster_firing_rates()) < min_unit_sumFR:
        print("Firing rate too low. Passing")
        return

    model.run()

    out_dir = wet.get_sglx_project(outputProjectName).get_experiment_subject_directory(
        experiment,
        subjectName,
    )
    out_dir.mkdir(exist_ok=True, parents=True)

    off_fname = f"{probe}.{structure}.{args.pooled_states}.spatial_off_df.pickle"
    model.off_df["pooled_states"] = args.pooled_states
    with open(out_dir / off_fname, "wb") as f:
        pickle.dump(model.off_df, f)

    all_windows_on_off_fname = (
        f"{probe}.{structure}.{args.pooled_states}.all_windows_on_off_df.pickle"
    )
    model.all_windows_on_off_df["pooled_states"] = args.pooled_states
    with open(out_dir / all_windows_on_off_fname, "wb") as f:
        pickle.dump(model.all_windows_on_off_df, f)

    windows_fname = f"{probe}.{structure}.{args.pooled_states}.windows_df.pickle"
    model.windows_df["pooled_states"] = args.pooled_states
    with open(out_dir / windows_fname, "wb") as f:
        pickle.dump(model.windows_df, f)

    windows_info_fname = (
        f"{probe}.{structure}.{args.pooled_states}.windows_output_infos.pickle"
    )
    with open(out_dir / windows_info_fname, "wb") as f:
        pickle.dump(model.windows_output_infos, f)


if __name__ == "__main__":
    main()

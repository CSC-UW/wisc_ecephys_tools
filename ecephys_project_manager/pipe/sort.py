from datetime import datetime

import spikeinterface.extractors as se
import spikeinterface.sorters as ss
from ecephys import sglx
from ecephys_project_manager.params import get_analysis_params
from ecephys_project_manager.projects import get_alias_subject_directory

from .prepro import CATGT_PROJECT_NAME, get_catgt_output_paths


def get_sorting_output_path(
    project=None,
    subject=None,
    experiment=None,
    alias=None,
    probe=None,
    analysis_name=None,
):
    """Return f'project_dir/exp/alias/subject/{analysis_name}.{probe}'"""
    output_dirname = f"{analysis_name}.{probe}"
    return (
        get_alias_subject_directory(
            project,
            experiment,
            alias,
            subject,
        )
        / output_dirname
    )


def run_sorting(
    project=None,
    subject=None,
    experiment=None,
    alias=None,
    probe=None,
    analysis_name=None,
    prepro_analysis_name=None,
    prepro_project=CATGT_PROJECT_NAME,
    bad_channels=None,  # TODO
    rerun_existing=False,
    dry_run=True,
):
    """Run sorting in alias-subject directory.

    Parameters:
    -----------
    project, subject, experiment, alias, probe: str
    analysis_name: str
        A key in 'sorting' document in analysis_cfg.py
    prepro_analysis_name: str
        A key in 'prepro' document in analysis_cfg.py used to preprocess the data
    prepro_project: str
        Project where the preprocessed data was saved
    """
    assert all(
        [
            arg is not None
            for arg in [project, subject, experiment, alias, probe, analysis_name]
        ]
    )
    print(f"Run: {locals()}")

    # Output
    output_dir = get_sorting_output_path(
        project,
        subject,
        experiment,
        alias,
        probe,
        analysis_name,
    )
    print(f"Saving sorting output at {output_dir}")

    # rerun existing
    if (output_dir / "spike_times.npy").exists() and not rerun_existing:
        print(f"Passing: output directory is already done: {output_dir}\n\n")
        return True
    elif rerun_existing:
        if output_dir.exists():
            print(f"rerun_exising==True : rm directory at {output_dir}")
            import shutil

            shutil.rmtree(output_dir)

    # Sorter parameters
    sorter, params = get_analysis_params(
        "sorting",
        analysis_name,
    )

    # Recording
    if not dry_run:
        rec = prepare_data(
            subject=subject,
            experiment=experiment,
            alias=alias,
            probe=probe,
            prepro_analysis_name=prepro_analysis_name,
            prepro_project=prepro_project,
            bad_channels=bad_channels,
        )

    if dry_run:
        print("Dry run: doing nothing")
        return True

    print("Running...", end="")
    start = datetime.now()
    output_dir.mkdir(exist_ok=True, parents=True)
    if sorter == "kilosort2_5":
        ss.sorter_dict[sorter].set_kilosort2_5_path(params["ks_path"])
    ss.run_sorter(sorter, rec, output_folder=output_dir, verbose=True, **params)
    # Clear `recording.dat`
    rec_path = output_dir / "recording.dat"
    rec_path.unlink()

    end = datetime.now()
    print(
        f"{end.strftime('%H:%M:%S')}: Finished {project}, {subject}, {experiment}, {alias}, {probe}."
    )
    print(f"Run time = {str(end - start)}\n")

    # Sorting finished if we find spike_times.npy
    return (output_dir / "spike_times.npy").exists()


def prepare_data(
    subject=None,
    experiment=None,
    alias=None,
    probe=None,
    prepro_analysis_name=None,
    prepro_project=CATGT_PROJECT_NAME,
    bad_channels=None,
):

    if prepro_analysis_name is None:
        raise NotImplementedError(
            "Sorting must be performed on preprocessed data."
            "Please specify the `prepro_analysis_name` kwarg so we can find the data."
        )

    meta_bin_paths = get_catgt_output_paths(
        project=prepro_project,
        subject=subject,
        experiment=experiment,
        alias=alias,
        probe=probe,
        analysis_name=prepro_analysis_name,
    )
    metapaths, binpaths = zip(*meta_bin_paths)

    for m in metapaths:
        assert m.exists()  # Check that catgt finished. Should be unnecessary.

    rec_extractors = [
        se.SpikeGLXRecordingExtractor(
            binpath.parent, stream_id="".join(binpath.suffixes[:-1]).strip(".")
        )
        for binpath in binpaths
    ]

    if len(rec_extractors) == 1:
        recording = rec_extractors[0]
    else:
        recording = se.MultiRecordingTimeExtractor(rec_extractors)
    total_t = recording.get_num_frames() / recording.get_sampling_frequency()
    n_chans = recording.get_num_channels()
    print(
        f"Recording extractor: Concatenate N={len(binpaths)} bin files,"
        f" N={n_chans}chans, T={total_t/3600}h"
    )

    assign_locations(recording, binpaths[0])

    if bad_channels is not None:
        raise NotImplementedError()
        # recording = st.preprocessing.remove_bad_channels(
        #     recording, bad_channel_ids=bad_channels
        # )

    return recording


def assign_locations(recording, binpath, plot=False):
    from ecephys.sglx import get_xy_coords

    idx, x, y = get_xy_coords(binpath)

    assert "#SY0" in recording.channel_ids[-1], "Expected to find SYNC channel."

    recording.set_channel_locations(
        [(x[i], y[i]) for i in range(len(idx))], channel_ids=recording.channel_ids[:-1]
    )
    if plot:
        from ecephys.plot import plot_channel_coords

        plot_channel_coords(range(len(x)), x, y)

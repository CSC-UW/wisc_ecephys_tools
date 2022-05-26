from datetime import datetime

import numpy as np
import spikeinterface as si
import spikeinterface.extractors as se
import spikeinterface.sorters as ss
from ecephys.plot import plot_channel_coords
from ecephys.sglx import get_xy_coords
from wisc_ecephys_tools.params import get_analysis_params
from wisc_ecephys_tools.projects import get_alias_subject_directory
from probeinterface import Probe

from .prepro import CATGT_PROJECT_NAME, get_catgt_output_paths


# TODO: The `analysis_name` parameter does not actually correspond to any other `analysis_name` parameters.
# Instead, it is a concatenation of several analyses: the sorting analysis name, the postprocessing analysis name, and the quality metrics analysis name.
# For example, `ks2_5_catgt_df_postpro_2_metrics_all_isi`.
def get_sorting_output_path(
    project=None,
    subject=None,
    experiment=None,
    alias=None,
    probe=None,
    sorting_name=None,
):
    """Return f'project_dir/exp/alias/subject/{sorting_name}.{probe}'.

    The name of the output directory ('sorting_name') is {sorting_name}.{probe}
    and it is located in the 'alias_subject_directory'
    (`ecephys.projects.get_alias_subject_directory`)
    """
    output_dirname = f"{sorting_name}.{probe}"
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
        ss.sorter_dict[sorter].set_kilosort2_5_path(params.pop("ks_path"))
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
        recording = si.concatenate_recordings(rec_extractors)
    total_t = recording.get_num_frames() / recording.get_sampling_frequency()
    n_chans = recording.get_num_channels()
    print(
        f"Recording extractor: Concatenate N={len(binpaths)} bin files,"
        f" N={n_chans}chans, T={total_t/3600}h"
    )

    recording = set_probe_and_locations(recording, binpaths[0])

    if bad_channels is not None:
        raise NotImplementedError()
        # recording = st.preprocessing.remove_bad_channels(
        #     recording, bad_channel_ids=bad_channels
        # )

    print(f"Finished setting up recording and probe information.")
    print(f"Recording: {recording}")
    print(f"Probe: {recording.get_probe()}")

    return recording


def set_probe_and_locations(recording, binpath):

    idx, x, y = get_xy_coords(binpath)

    locations = np.array([(x[i], y[i]) for i in range(len(idx))])
    shape = "square"
    shape_params = {"width": 8}

    prb = Probe()
    if "#SY0" in recording.channel_ids[-1]:
        print("FOUND SY0")
        ids = recording.channel_ids[:-1]  # Remove last (SY0)
    else:
        ids = recording.channel_ids
    prb.set_contacts(locations[: len(ids), :], shapes=shape, shape_params=shape_params)
    prb.set_contact_ids(ids)  # Must go after prb.set_contacts
    prb.set_device_channel_indices(
        np.arange(len(ids))
    )  # Mandatory. I did as in recording.set_dummy_probe_from_locations
    assert prb._contact_positions.shape[0] == len(
        prb._contact_ids
    )  # Shouldn't be needed

    recording = recording.set_probe(prb)

    if any(["#SY0" in id for id in recording.channel_ids]):
        assert False, "Did not expect to find SYNC channel"

    return recording

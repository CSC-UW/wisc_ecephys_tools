from datetime import datetime
from pathlib import Path

import spikeinterface.extractors as se
import spikeinterface.sorters as ss
from ecephys import sglx


def run_sorting(subject, condition, sorting_condition,
                catgt_data=True, tgt_root_key=None, bad_channels=None,
                rerun_existing=True, dry_run=False, clean_dat_file=False):
    print(f"Run: {locals()}")

    # Output
    output_dir = paths.get_datapath(
        subject,
        condition,
        sorting_condition,
        root_key=tgt_root_key,
    )
    print(f"Saving sorting output at {output_dir}")
    
    # rerun existing
    if (output_dir/'spike_times.npy').exists() and not rerun_existing:
        print(f'Passing: output directory is done: {output_dir}\n\n')
        return

    # Sorter parameters
    sorter, params = parameters.get_analysis_params(
        'sorting',
        sorting_condition
    )
    
    # Recording
    rec = prepare_data(
        subject, 
        condition,
        catgt_data=catgt_data,
        bad_channels=bad_channels
    )
    

    start = datetime.now()
    if dry_run:
        print("Dry run: doing nothing")
    else:
        print('Running...', end='')
        output_dir.mkdir(exist_ok=True, parents=True)
        ss.run_sorter(
            sorter,
            rec,
            output_folder=output_dir,
            verbose=True,
            **params
        )
        rec_path = output_dir/'recording.dat'
        if clean_dat_file and rec_path.exists():
            rec_path.unlink()

    end = datetime.now()
    print(f"{end.strftime('%H:%M:%S')}: Finished {subject}, {condition}, {sorting_condition}.")
    print(f"Run time = {str(end - start)}\n")

    return 1


def prepare_data(subject, condition, catgt_data=True, bad_channels=None):

    if catgt_data:
        root_key = 'catgt'
    else:
        root_key = 'raw_chronic'

    binpaths = paths.get_sglx_style_datapaths(
        subject,
        condition,
        'ap.bin',
        catgt_data=catgt_data,
        root_key=root_key,
    )
    for p in binpaths:
        # Check that catgt finished
        assert sglx.get_meta_path(p).exists()
    
    rec_extractors = [
        se.SpikeGLXRecordingExtractor(binpath)
        for binpath in binpaths
    ]

    if len(rec_extractors) == 1:
        recording = rec_extractors[0]
    else:    
        recording = se.MultiRecordingTimeExtractor(rec_extractors)
    total_t = recording.get_num_frames() / recording.get_sampling_frequency()
    n_chans = recording.get_num_channels()
    print( f'binpaths: {binpaths}')
    print(
        f'Recording extractor: N={len(binpaths)} bin files,'
        f' N={n_chans}chans, T={total_t/3600}h'
    )

    assign_locations(recording, binpaths[0])

    if bad_channels is not None:
        recording = st.preprocessing.remove_bad_channels(
            recording, bad_channel_ids=bad_channels
        )

    return recording


def assign_locations(recording, binpath, plot=False):
    from ecephys.sglx import get_xy_coords
    idx, x, y = get_xy_coords(binpath)
    recording.set_channel_locations(
        [(x[i], y[i]) for i in range(len(idx))],
        channel_ids=idx,
    )
    if plot:
        from ecephys.plot import plot_channel_coords
        plot_channel_coords(range(len(x)), x, y)

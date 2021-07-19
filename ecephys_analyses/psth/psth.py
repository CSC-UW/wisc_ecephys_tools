from pathlib import Path

import numpy as np
import pandas as pd
import spikeextractors as se
from ecephys_analyses.data import channel_groups, parameters, paths
from spykes.plot.neurovis import NeuroVis
from spykes.plot.popvis import PopVis
import ecephys.io.load


BINSIZE_DF = 15
PSTH_WINDOW_DF = [-5000, 2000]


def get_average_psth_data(
    subject, condition, sorting_condition,
    region='all',
    state=None,
    good_only=False,
    normalize='baseline_zscore',
):

    # Get raw psth
    pop, raw_psth_dict, info, event_df = get_all_psth_data(
        subject, condition, sorting_condition,
        region=region,
        state=state,
        good_only=good_only,
    )

    # Get normalized psth
    window = raw_psth_dict['window']
    binsize = raw_psth_dict['binsize']
    conditions = raw_psth_dict['conditions']
    average_psth_dict = {
        'window': window,
        'binsize': binsize,
        'event': raw_psth_dict['event'],
        'conditions': conditions,
        'n_clusters': pop.n_neurons,
        'data': {},
    }
    assert set(average_psth_dict.keys()) >= set(raw_psth_dict.keys())

    # 0 everywhere If no clusters:
    if pop.n_neurons == 0:
        average_psth_dict['data'][0] = np.zeros(
             (len(np.arange(window[0], window[1], binsize)), )
        )
    else:
        for i, key in enumerate(raw_psth_dict['data'].keys()):
            # norms the data.
            # orig_data = psth_dict['data'][cond_id]
            orig_data = raw_psth_dict['data'][key]
            normed_data = pop._get_normed_data(
                orig_data, normalize=normalize, window=window, binsize=binsize,
            ) # n_cluster, n_bins
            average_data = np.mean(normed_data, 0)
            average_psth_dict['data'][key] = average_data
    
    return average_psth_dict, info, event_df


def get_all_psth_data(
    subject, condition, sorting_condition,
    region='all',
    state=None,
    window=None,
    binsize=None,
    good_only=False,
):
    # Params
    if window is None:
        window=PSTH_WINDOW_DF
    if binsize is None:
        binsize=BINSIZE_DF
    print(f'Get all psth, window={window}, binsize={binsize}')

    # Path 
    ks_dir = paths.get_datapath(subject, condition, sorting_condition)

    # Get clusters
    if region == 'all':
        depth_interval = None
    else:
        depth_interval = channel_groups.region_depths[subject][condition][region]
    extr = ecephys.io.load.load_sorting_extractor(
        ks_dir,
        good_only=good_only,
        depth_interval=depth_interval,
    )
    info_all =  ecephys.io.load.get_cluster_info(ks_dir)
    info = info_all[info_all['cluster_id'].isin(extr.get_unit_ids())]

    # Create popVis
    neuron_list = initiate_neurons(extr)
    pop = PopVis(neuron_list)
    
    # event df
    event_df = load_event_times(subject, condition, state=state)
    print(f'N events = {len(event_df)}')
    event_colname = 'sglx_stim_time'
    assert event_colname in event_df.columns
    
    all_psth = pop.get_all_psth(
        event=event_colname, df=event_df, window=window,
        binsize=binsize, plot=False
    )
    return pop, all_psth, info, event_df

def initiate_neurons(extractor):
    
    # Add neurons ordered by depth
    neuron_list = list()
    for cluster_id in extractor.get_unit_ids():
        spike_times = [
            st for st
            in extractor.frame_to_time(extractor.get_unit_spike_train(cluster_id))
        ]
        # instantiate neuron
        neuron = NeuroVis(spike_times, name=f"#{cluster_id}")
        neuron_list.append(neuron)

    return neuron_list

def load_event_times(subject, condition, state=None, filename=None):
    if filename is None:
        filename='stim_times.csv'
    # Search in condition dir
    cond_path = paths.get_datapath(
        subject, condition, filename
    )
    if cond_path.exists():
        path = cond_path
    else:
        print(f"No event file at {cond_path}..", end='')
        root = paths.get_sglx_style_datapaths(
            subject, condition, 'ap.bin',
        )[0].parents[1]
        path = root/filename
    print(f"Load events at {path}")
    event_df = pd.read_csv(path)
    assert set(event_df.columns) == set(['stim_state', 'sglx_stim_time'])
    if state is None:
        res = event_df
    else:
        res = event_df[event_df['stim_state'] == state]
    if len(res) == 0:
        raise ValueError(f"N=0 selected events for file at {path}")
    return res

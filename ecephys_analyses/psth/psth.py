from pathlib import Path

import ecephys.units
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import spikeextractors as se
from ecephys.plot import plot_psth_heatmap
from ecephys.units import get_selection_intervals_str
from ecephys.units.psth import get_normed_data
from ecephys_analyses.data import channel_groups, parameters, paths
from ecephys_analyses.units import get_sorting_extractor
from spykes.plot.neurovis import NeuroVis
from spykes.plot.popvis import PopVis

BINSIZE_DF = 15
PSTH_WINDOW_DF = [-5000, 2000]


def make_psth_figures(
    subject, condition, sorting_condition,
    good_only=False, region='all', selection_intervals=None,
    normalize='baseline_zscore', 
    binsize=None, norm_window=None, plot_window=None,
    state=None, clim=None,
    root_key=None,
    save=False, show=True, output_dir=None,
    draw_region_limits=True,
):
    if output_dir is None:
        # Save in condition dir
        output_dir = paths.get_datapath(
            subject,
            condition,
            'plots',
            root_key=root_key
        )/sorting_condition
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(
        f"\n\nGenerate figures for {subject} {condition}, {state}, "
        f"{region}, good={good_only}, clim={clim}, output={output_dir}",
    )
    
    # PSTH with "norm window" (longer baseline used for normalization)
    pop, all_psth, info, event_df = get_all_psth_data(
        subject, condition, sorting_condition,
        region=region, good_only=good_only,
        selection_intervals=selection_intervals, state=state, 
        binsize=binsize, window=norm_window,
        root_key=root_key,
    )
    print("Done getting psth data")
    norm_window = all_psth['window']
    binsize = all_psth['binsize']
    
    # Normalize psth
    assert all_psth['conditions'] is None
    psth_raw = all_psth['data'][0]
    if not len(psth_raw):
        print("No data in psth. Passing")
        return
    psth_unsorted = get_normed_data(
        psth_raw, normalize=normalize,
        window=norm_window, binsize=binsize
    )
    
    # Order by depth (bottom is tip of probe)
    unsorted_depths = list(info['depth'])
    perm = sorted(range(len(unsorted_depths)), key=lambda k: unsorted_depths[k], reverse=True)
    depths = np.array(unsorted_depths)[perm]
    psth_array = psth_unsorted[perm,:]
    
    # Subwindow for plotting
    if plot_window is None:
        plot_window = norm_window
    assert plot_window[0] >= norm_window[0]
    assert plot_window[1] <= norm_window[1]
    xvalues = np.arange(norm_window[0], norm_window[1], binsize)
    plot_i = [i for i, x in enumerate(xvalues) if x >= plot_window[0] and x <= plot_window[1]]
    psth_array = psth_array[:, plot_i]
    window = plot_window
    
    # Get distance from surface of cortex
    region_depths = channel_groups.region_depths[subject][condition]
    if 'cortex' in region_depths:
        surface_depth = max(region_depths['cortex'])
    elif 'neocortex' in region_depths:
        surface_depth = max(region_depths['neocortex'])
    else:
        surface_depth = 7660.0
    print('Surface depth', surface_depth)
    depths_from_surf = [
        (surface_depth - d) / 1000 for d in depths
    ] 

    # Plot a certain number of labels overall
    n_ticks = 10
    n_clust = psth_array.shape[0]
    tick_modulo = int(n_clust/n_ticks) + 1
    ylabels = depths_from_surf
    ylabels = np.array([
        None if i % tick_modulo != 0 else lbl
        for i, lbl in enumerate(ylabels[::-1])
    ])[::-1]

    fig, axes = plot_psth_heatmap(
        psth_array, ylabels, window, binsize, clim=clim,
        cbar_label='Average rate (Z-scored)'
    )

    if draw_region_limits and region=='all':
        # Draw an horizontal line for each of the regions
        from ecephys.utils import find_nearest
        region_indices = {
            region: [
                find_nearest(depths, region_lims[0], tie_select='last'),
                find_nearest(depths, region_lims[1], tie_select='first'),
            ] for region, region_lims in region_depths.items()
        }  # {'region': [cluster_id_start, cluster_id_end]}
        for reg, (id_start, id_end) in region_indices.items():
            # Pass regions out of range
            if (id_start == id_end) and (id_start == 0 or id_start == n_clust):
                pass
            y1, y2 = id_start, id_end
            x, h = 0, 5
            plt.plot([x, x+h, x], [y1, (y1 + y2)/2, y2], c='k')
            plt.text(x + h + 1, (y1 + y2)/2, reg, ha='left', va='center', c='k')
    
    # Title
    title=f"PSTH: {subject}, {condition}\n"
    if state is not None:
        title+=f"State={state}; "
    if region not in [None, 'all']:
        title+=f'Region={region}; '
    title += f'N={len(event_df)} pulses; N={psth_array.shape[0]} clusters'
    plt.title(title)
    plt.ylabel('Clusters\n(mm from surface)')
    print("Done getting plot")
    
    if show:
        plt.show()
    
    if save:
        filename = f"psth_{subject}_{condition}_{state}_region={region}_goodonly={good_only}_norm={normalize}_clim={clim}_select={get_selection_intervals_str(selection_intervals)}"
        print(f'save {filename}')
        fig.savefig(Path(output_dir)/(filename + '.png'))
    
    return fig, axes


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
    selection_intervals=None,
    good_only=False,
    root_key=None,
):
    # Params
    if selection_intervals is None:
        selection_intervals = {}
    if window is None:
        window=PSTH_WINDOW_DF
    if binsize is None:
        binsize=BINSIZE_DF
    print(f'Get all psth, window={window}, binsize={binsize}')

    extr, info = get_sorting_extractor(
        subject,
        condition,
        sorting_condition,
        region=region,
        selection_intervals=selection_intervals,
        good_only=good_only,
        root_key=root_key,
    )

    # Create popVis
    neuron_list = initiate_neurons(extr)
    pop = PopVis(neuron_list)
    
    # event df
    event_df = load_event_times(subject, condition, state=state, root_key=root_key)
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


def load_event_times(subject, condition, state=None, filename=None, root_key=None,):
    if filename is None:
        filename='stim_times.csv'
    # Search in condition dir
    cond_path = paths.get_datapath(
        subject, condition, filename, root_key=root_key,
    )
    if cond_path.exists():
        path = cond_path
    else:
        print(f"No event file at {cond_path}..", end='')
        root = paths.get_sglx_style_datapaths(
            subject, condition, 'ap.bin', root_key=root_key,
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
        raise ValueError(f"N=0 selected events for state={state} in file at {path}")
    return res

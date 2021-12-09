from pathlib import Path

import ecephys.units
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import spikeextractors as se
from ecephys.plot import plot_psth_heatmap, plot_psth_hist
from ecephys.units import get_selection_intervals_str
from ecephys.units.psth import get_normed_data
from ecephys_project_manager.data import channel_groups, parameters, paths
from ecephys_project_manager.units import get_sorting_data
from spykes.plot.neurovis import NeuroVis
from spykes.plot.popvis import PopVis

BINSIZE_DF = 15
PSTH_WINDOW_DF = [-5000, 2000]


def get_data(
    subject, condition, sorting_condition,
    selected_groups=None, region='all', selection_intervals=None,
    state=None,
    root_key=None,
):
    # Spikes
    extr, info = get_sorting_data(
        subject,
        condition,
        sorting_condition,
        region=region,
        selection_intervals=selection_intervals,
        selected_groups=selected_groups,
        root_key=root_key,
    )
    cluster_ids = extr.get_unit_ids()
    spike_times_list = ecephys.units.get_spike_times_list(extr, cluster_ids)

    # events
    event_df = load_event_times(subject, condition, state=state, root_key=root_key)

    return spike_times_list, cluster_ids, info, event_df


def get_output_dir(subject, condition, sorting_condition, root_key=None):
    # Save in condition dir
    return paths.get_datapath(
        subject,
        condition,
        'plots',
        root_key=root_key
    )/sorting_condition


def make_pooled_psth_hist(
    subject, condition, sorting_condition, root_key=None,
    state=None, region='all', 
    selected_groups=None, selection_intervals=None,
    normalize='baseline_zscore', binsize=None, norm_window=None,
    plot_window=None, ylim=None,
    save=False, show=True, output_dir=None,
):
    if output_dir is None:
        output_dir = get_output_dir(subject, condition, sorting_condition, root_key=root_key)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(
        f"\n\nGenerate psth hists for {subject} {condition}, {state}, "
        f"{region}, groups={selected_groups}, ylim={ylim}, output={output_dir}",
    )
    
    spike_times_list, _, info, event_df = get_data(
        subject, condition, sorting_condition,
        selected_groups=selected_groups, region=region, selection_intervals=selection_intervals,
        state=state,
        root_key=root_key,
    )

    if not len(info):
        import warnings
        warnings.warn("N=0 selected clusters. Passing dataset.")
        return None, None
    if not len(event_df):
        import warnings
        warnings.warn("N=0 selected events. Passing dataset.")
        return None, None

    # Combine all spikes
    pooled_spike_times = ecephys.units.pool_spike_times_list(spike_times_list)
    pooled_cluster_ids = ['MUA']

    # PSTH with "norm window" (longer baseline used for normalization)
    _, all_psth = get_all_psth_data(
        [pooled_spike_times], pooled_cluster_ids, event_df,
        binsize=binsize, window=norm_window,
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
    psth_normed = get_normed_data(
        psth_raw, normalize=normalize,
        window=norm_window, binsize=binsize
    )

    # Subwindow for plotting
    if plot_window is None:
        plot_window = norm_window
    assert plot_window[0] >= norm_window[0]
    assert plot_window[1] < norm_window[1]
    xvalues = np.arange(norm_window[0], norm_window[1] + 1, binsize)
    plot_i = [i for i, x in enumerate(xvalues) if x >= plot_window[0] and x < plot_window[1]]
    psth_array = psth_normed[:, plot_i]
    window = plot_window

    assert psth_array.shape[0] == 1
    psth_array = psth_array[0, :]
    fig, ax = plot_psth_hist(
        psth_array, window, binsize, ylim=ylim,
    )

    # Title
    title=f"PSTH: {subject}, {condition}\n"
    if state is not None:
        title+=f"State={state}; "
    if region not in [None, 'all']:
        title+=f'Region={region}; '
    title += f'N={len(event_df)} pulses; N={len(info)} clusters'
    plt.title(title)
    #

    if normalize == 'baseline_zscore':
        ylabel = 'Z-scored firing rate'
    elif normalize == 'baseline_norm':
        ylabel = 'Normalized firing rate'
    else:
        assert False
    plt.ylabel(ylabel)
    
    if show:
        plt.show()
    
    if save:
        filename = f"psth_hist_{subject}_{condition}_{state}_region={region}_groups={selected_groups}_select={get_selection_intervals_str(selection_intervals)}_norm={normalize}_ylim={ylim}"
        print(f'save at {Path(output_dir)/filename}')
        fig.savefig(Path(output_dir)/(filename + '.png'))
        fig.savefig(Path(output_dir)/(filename + '.svg'))
    
    return fig, ax


def make_psth_heatmap(
    subject, condition, sorting_condition, root_key=None,
    state=None, region='all',
    selected_groups=None, selection_intervals=None,
    normalize='baseline_zscore', binsize=None, norm_window=None,
    plot_window=None, clim=None,
    draw_regions_list=None, region_suffixes_to_clip=None,
    save=False, show=True, output_dir=None, extensions=None,
):
    if output_dir is None:
        output_dir = get_output_dir(subject, condition, sorting_condition, root_key=root_key)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    if draw_regions_list is None:
        draw_regions_list = []
    if region_suffixes_to_clip is None:
        region_suffixes_to_clip = []
    if extensions is None:
        extensions = ['.png', '.svg']

    print(
        f"\n\nGenerate psth heatmaps for {subject} {condition}, {state}, "
        f"{region}, groups={selected_groups}, clim={clim}, output={output_dir}",
    )
    
    spike_times_list, cluster_ids, info, event_df = get_data(
        subject, condition, sorting_condition,
        selected_groups=selected_groups, region=region, selection_intervals=selection_intervals,
        state=state,
        root_key=root_key,
    )

    if not len(info):
        import warnings
        warnings.warn("N=0 selected clusters. Passing dataset.")
        return None, None
    if not len(event_df):
        import warnings
        warnings.warn("N=0 selected events. Passing dataset.")
        return None, None

    # PSTH with "norm window" (longer baseline used for normalization)
    _, all_psth = get_all_psth_data(
        spike_times_list, cluster_ids, event_df,
        binsize=binsize, window=norm_window,
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
    xvalues = np.arange(norm_window[0], norm_window[1] + binsize, binsize)
    plot_i = [i for i, x in enumerate(xvalues) if x >= plot_window[0] and x < plot_window[1]]
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

    if normalize == 'baseline_zscore':
        cbar_label = 'Average rate (Z-scored)'
    elif normalize == 'baseline_norm':
        cbar_label = 'Normalized rate'
    else:
        assert False

    fig, axes = plot_psth_heatmap(
        psth_array, ylabels, window, binsize, clim=clim,
        cbar_label=cbar_label
    )

    # Title
    title=f"PSTH: {subject}, {condition}\n"
    if state is not None:
        title+=f"State={state}; "
    if region not in [None, 'all']:
        title+=f'Region={region}; '
    title += f'N={len(event_df)} pulses; N={len(cluster_ids)} clusters'
    plt.title(title)
    plt.ylabel('Clusters (mm from surface)')
    plt.xlabel('Time to pulse (msec)')
    print("Done getting plot")

    # Draw an horizontal line for each of the regions ending with draw_region_suffix. We remove the suffix.
    from ecephys.utils import find_nearest
    from functools import reduce
    drawable_region_depths = {
        reduce(lambda region, suffix: region.replace(suffix, ''), region_suffixes_to_clip, region): depths  # One liner to remove all substrings like a boss
        for region, depths in region_depths.items()
        if region in draw_regions_list
    }
    drawable_region_indices = {
        region: [
            find_nearest(depths, region_lims[0], tie_select='first'),  # Depths are descending here
            find_nearest(depths, region_lims[1], tie_select='last'),  # Depths are descending here
        ] for region, region_lims in drawable_region_depths.items()
    }  # {'region': [cluster_id_start, cluster_id_end]}
    for reg, (id_end, id_start) in drawable_region_indices.items():
        # Pass regions out of range
        if (id_start == id_end) and (id_start == 0 or id_start == n_clust - 1):
            print(f"Out of range: not drawing region {reg}")
            continue
        y1, y2 = id_start + 0.5, id_end + 0.5
        # x, h, ha, text_gap = 0, 5, 'left', +1  # Inside axis, left
        x, h, ha, text_gap = -20, -5, 'right', -1  # Left of y axis
        plt.plot([x, x+h, x], [y1, (y1 + y2)/2, y2], c='k', clip_on=False)
        plt.text(x + h + text_gap, (y1 + y2)/2, reg, ha=ha, va='center', c='k', clip_on=False)
    
    if show:
        plt.show()
    
    if save:
        filename = f"psth_heatmap_{subject}_{condition}_{state}_region={region}_groups={selected_groups}_select={get_selection_intervals_str(selection_intervals)}_norm={normalize}_clim={clim}"
        print(f'save at {Path(output_dir)/filename}')
        for ext in extensions:
            fig.savefig(Path(output_dir)/(filename + ext), bbox_inches='tight')
    
    return fig, axes


def get_all_psth_data(
    spike_times_list, cluster_ids, event_df,
    event_colname='sglx_stim_time',
    window=None,
    binsize=None,
):
    # Params
    if window is None:
        window=PSTH_WINDOW_DF
    if binsize is None:
        binsize=BINSIZE_DF
    print(f'Get all psth, window={window}, binsize={binsize}, N events = {len(event_df)}')

    assert event_colname in event_df.columns

    # Create popVis
    neuron_list = initiate_neurons(spike_times_list, cluster_ids)
    pop = PopVis(neuron_list)
    
    # Get psth
    all_psth = pop.get_all_psth(
        event=event_colname, df=event_df, window=window,
        binsize=binsize, plot=False
    )
    return pop, all_psth


def initiate_neurons(spike_times_list, cluster_ids):

    assert len(spike_times_list) == len(cluster_ids)
    
    # Add neurons ordered by depth
    neuron_list = list()
    for i, cluster_id in enumerate(cluster_ids):
        # instantiate neuron
        neuron = NeuroVis(spike_times_list[i], name=f"#{cluster_id}")
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
        raise ValueError(f"No event file at {cond_path}..")
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
        res = event_df.loc[event_df['stim_state'] == state, :].copy()
    if len(res) == 0:
        import warnings
        warnings.warn(
            f"N=0 selected events for state={state} in file at {path}"
        )
    return res

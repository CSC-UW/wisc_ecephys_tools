from pathlib import Path

import numpy as np
import pandas as pd
import spikeextractors as se
from ecephys_analyses.data import channel_groups, parameters, paths
import ecephys.units

from on_off_detection import OnOffModel


def run_on_off_detection(
    subject,
    condition,
    detection_condition,
    sorting_condition=None,
    region=None,
    region_name=None,
    depth_interval=None,
    FR_interval=None,
    state=None,
    good_only=False,
    pool=True,
    n_jobs=1,
):
    # Detection condition
    p = parameters.get_analysis_params('on_off_detection', detection_condition)
    method = p['method']
    params = p['params']
    if sorting_condition is None:
        sorting_condition = p['sorting_condition']

    print("Run on-off detection:", subject, condition, sorting_condition, state, good_only, pool, '\n')

    # Sorting info
    ks_dir = paths.get_datapath(subject, condition, sorting_condition)
    Tmax = ecephys.units.get_sorting_info(ks_dir)['duration']

    # Get depth intervals either from file ('region') or from kwargs
    if region is None:
        assert region_name and depth_interval
    if region is not None:
        assert not region_name and not depth_interval
        region_name = region
        if region == 'all':
            depth_interval = None
        else:
            depth_interval = channel_groups.region_depths[subject][condition][region]
    print(f"Region: {region_name}, {depth_interval}")

    # Get clusters
    extr = ecephys.units.load_sorting_extractor(
        ks_dir,
        good_only=good_only,
        depth_interval=depth_interval,
        FR_interval=FR_interval,
    )
    cluster_ids = extr.get_unit_ids()
    info_all =  ecephys.units.get_cluster_info(ks_dir)
    info = info_all[info_all['cluster_id'].isin(cluster_ids)]
    spike_trains_list = [
        extr.get_unit_spike_train(cluster_i) / extr.get_sampling_frequency()
        for cluster_i in cluster_ids
    ]

    # Cut and concatenate bouts of interest
    hyp = pd.read_csv(
        paths.get_datapath(subject, condition, 'hypnogram.csv')
    )
    if state is not None:
        if not state in hyp.state.unique():
            raise Exception(f'No {state} bout in hyp ({hyp.state.unique()}')
        bouts_df = hyp[hyp['state'] == state].reset_index()
        spike_trains_list = ecephys.units.subset_spike_times_list(
            spike_trains_list,
            bouts_df
        )
        Tmax = bouts_df.duration.sum()
    else:
        bouts_df = hyp

    # Output dir
    output_dir = paths.get_datapath(subject, condition, detection_condition)
    debug_plot_filename = f'on_off_summary_pool={pool}_region={region_name}_good={True}'
    output_dir.mkdir(exist_ok=True, parents=True)

    if not len(cluster_ids):
        import warnings
        warnings.warn("No cluster in region. Passing")
        on_off_df = pd.DataFrame()
    elif all(len(train) == 0 for train in spike_trains_list):
        import warnings
        warnings.warn("No spikes in bouts. Passing")
        on_off_df = pd.DataFrame()
    else:
        # Compute
        on_off_model = OnOffModel(
            spike_trains_list,
            cluster_ids=cluster_ids,
            pooled_detection=pool,
            params=params,
            Tmax=Tmax,
            method=method,
            output_dir=output_dir,
            debug_plot_filename=debug_plot_filename,
            hyp=bouts_df,
            n_jobs=n_jobs,
        )
        on_off_df = on_off_model.run()
    
    # Add hypnogram info for computed on_off periods
    # - Condition from original hypnogram
    # - Mark on/off periods that span non-consecutive bouts
    on_off_df['condition'] = 'interbout'
    bout_start_T = 0
    bout_start_T = 0
    for i, row in bouts_df.iterrows():
        bout_end_T = bout_start_T + row['duration']
        bout_on_off = (
            (on_off_df['start_time'] >= bout_start_T)
            & (on_off_df['end_time'] <= bout_end_T)
        )
        bout_cond = row['condition'] if 'condition' in bouts_df.columns else 'intrabout'
        on_off_df.loc[bout_on_off, 'condition'] = bout_cond
        on_off_df.loc[bout_on_off, 'orig_hyp_bout_idx'] = row['index']
        bout_start_T = bout_end_T
    # Total state time per condition
    for cond in bouts_df['condition'].unique():
        total_cond_time = bouts_df[bouts_df['condition'] == cond].duration.sum()
        on_off_df.loc[on_off_df['condition'] == cond, 'condition_state_time'] = total_cond_time

    on_off_filename = get_on_off_df_filename(
        region=region_name, good_only=good_only, pool=pool,
    )
    print(f"Save on_off_df at {output_dir/on_off_filename}")
    on_off_df.to_csv(output_dir/(on_off_filename+'.csv'), index=False)

    return on_off_df


def get_on_off_df_filename(
    region=None, good_only=False, pool=True,
):
    return f'on_off_df_pool={pool}_region={region}_good={good_only}'
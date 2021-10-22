from pathlib import Path

import numpy as np
import pandas as pd
import spikeextractors as se
from ecephys_analyses.data import channel_groups, parameters, paths
import ecephys.units
from ecephys.units.select import get_selection_intervals_str
import ecephys_analyses.units

from on_off_detection import OnOffModel


def run_on_off_detection(
    subject,
    condition,
    detection_condition,
    sorting_condition=None,
    region=None,
    good_only=False,
    selection_intervals=None,
    state=None,
    pool=False,
    n_jobs=1,
    root_key=None,
):
    """Run on-off periods detection.

    Args:
        subject, condition (str): Subject and condition of interest.
        detection_condition (str): Key for `on_off_detection` parameters in `analysis_parameters.yml`
    
    Kwargs:
        sorting_condition (str or None): Name of KS output directory. Overrides 'on_off_detection` param if provided.
        region (str or None): used to get depth interval from `regions.yml`
        good_only (bool): Subselect `cluster_group == 'good'`.
            We use KSLabel assignment when curated `group` is None or 'unscored'
        selection_intervals (dict): Dictionary of {<col_name>: (<value_min>, <value_max>)} used
            to subset clusters based on depth, firing rate, metrics value, etc
            All keys should be columns of `cluster_info.tsv` or `metrics.csv`, and the values should be numrical.
        state (str): Run only on this state. Should be present in hypnogram.
        pool (bool): Pool all selected units within region for on_off detection? Otherwise compute on_off for each unit separately
        n_jobs (int): Parallelize over units if pool==False
        root_key : Root for all data. Passed to all `paths` methods.
    """
    # Detection condition
    p = parameters.get_analysis_params('on_off_detection', detection_condition)
    method = p['method']
    params = p['params']
    if sorting_condition is None:
        sorting_condition = p['sorting_condition']

    print("Run on-off detection:", subject, condition, sorting_condition, state, good_only, pool, '\n')

    # Sorting info
    ks_dir = paths.get_datapath(subject, condition, sorting_condition, root_key=root_key)
    Tmax = ecephys.units.get_sorting_info(ks_dir)['duration']

    # Get spike trains of interest
    extr, info = ecephys_analyses.units.get_sorting_data(
        subject,
        condition,
        sorting_condition,
        region=region,
        selection_intervals=selection_intervals,
        good_only=good_only,
        root_key=root_key,
    )
    cluster_ids = sorted(extr.get_unit_ids())
    spike_trains_list = ecephys.units.get_spike_trains_list(
        extr
    )

    # Cut and concatenate bouts of interest
    hyp = pd.read_csv(
        paths.get_datapath(subject, condition, 'hypnogram.csv', root_key=root_key)
    )
    if state is not None:
        print(f"Select bouts of interest (state={state})", end="")
        if not state in hyp.state.unique():
            raise Exception(f'No {state} bout in hyp ({hyp.state.unique()}')
        bouts_df = hyp[hyp['state'] == state].reset_index()
        spike_trains_list = ecephys.units.subset_spike_times_list(
            spike_trains_list,
            bouts_df
        )
        Tmax = bouts_df.duration.sum()
        print(f"Subselect T={Tmax} seconds within state")
        print(bouts_df.groupby('condition').sum()['duration'])
    else:
        bouts_df = hyp

    # Output dir
    output_dir = paths.get_datapath(subject, condition, detection_condition, root_key=root_key)
    debug_plot_filename = f'on_off_summary_pool={pool}_region={region}_good={good_only}_state={state}_sorting={sorting_condition}_intervals={get_selection_intervals_str(selection_intervals)}'
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
        region=region,
        good_only=good_only,
        pool=pool,
        sorting_condition=sorting_condition,
        state=state,
        selection_intervals=selection_intervals,
    )
    print(f"Save on_off_df at {output_dir/on_off_filename}")
    on_off_df.to_csv(output_dir/(on_off_filename+'.csv'), index=False)

    return on_off_df


def get_on_off_df_filename(
    region=None,
    good_only=None,
    pool=None,
    sorting_condition=None,
    state=None,
    selection_intervals=None,
):
    return f'on_off_df_pool={pool}_region={region}_good={good_only}_state={state}_sorting={sorting_condition}_intervals={get_selection_intervals_str(selection_intervals)}'
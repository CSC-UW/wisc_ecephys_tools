from ecephys_project_manager.on_off import run_on_off_detection, get_on_off_df_filename
from ecephys_project_manager.data_mgmt.paths import get_datapath
import pandas as pd

from ecephys_project_manager.data.channel_groups import region_depths
from ecephys_project_manager.data import paths
import ecephys_project_manager.units
import ecephys.units


def load_analysis_data(
    data_conditions,
    detection_condition,
    state,
    region_orig,
    selected_groups_orig,
    selection_intervals_orig,
    region,
    selected_groups,
    selection_intervals,
    pool,
    root_key='SD',
):

    dfs = []
    info_dfs = []
    for (
        subject, condition, sorting_condition,
    ) in data_conditions:

        assert 'imec0' in condition or 'imec1' in condition
        probe = 'imec0' if 'imec0' in condition else 'imec1'
        dataset = f"{subject}_{probe}"

        filename = get_on_off_df_filename(
            region=region_orig,
            selected_groups=selected_groups_orig,
            pool=pool,
            sorting_condition=sorting_condition,
            state=state,
            selection_intervals=selection_intervals_orig,
        )
        filepath = get_datapath(
            subject,
            condition,
            detection_condition,
            root_key=root_key,
        )/filename

        try:
           df = pd.read_csv(str(filepath)+'.csv')
        except pd.errors.EmptyDataError:
            print('pass no data', subject, condition, region)
            continue

        df['subject'] = subject
        df['orig_condition'] = condition
        df['region'] = region
        df['pool'] = pool
        df['probe'] = probe
        df['recovery_condition'] = f'recovery-sleep-2h_{probe}'
        df['baseline_condition'] = f'baseline-sleep-2h-circadian-match_{probe}'
        df['dataset'] = dataset

        # Subset clusters using cluster_info
        _, info = ecephys_project_manager.units.get_sorting_data(
            subject,
            condition,
            sorting_condition,
            selected_groups=selected_groups,
            region=region,
            selection_intervals=selection_intervals,
            root_key=root_key
        )
        if 'cluster_id' not in info.columns:
            info['cluster_id'] = info['id']
        info['subject'] = subject
        info['orig_condition'] = condition
        info['region'] = region
        info['pool'] = pool
        info['probe'] = probe
        info['recovery_condition'] = f'recovery-sleep-2h_{probe}'
        info['baseline_condition'] = f'baseline-sleep-2h-circadian-match_{probe}'
        info['dataset'] = dataset

        # All "info" (subsetted clusters) should have been computed (should be in df)
        # Except if their firing rate was null during the state of interest
        if any([c not in df.cluster_id.values for c in info.cluster_id.values]):
            # TODO fill missing clusters in on_off
            import warnings 
            N_missing = sum([c not in df.cluster_id.values for c in info.cluster_id.values])
            print('\n\n\n')
            warnings.warn(f"on_off data is missing for N={N_missing} expected clusters.. Maybe their firing rate was 0 for the state of interest? Subset cluster_info accordingly.")
            print('\n\n\n')
            assert (N_missing / len(info.cluster_id.unique())) < 0.05, 'More than 5 percent of missing clusters, probably something is wrong...'
            info = info[info['cluster_id'].isin(df['cluster_id'].values)].copy()

        print(f"dataset = {dataset}: Load N={len(df['cluster_id'].unique())} clusters, subset N={len(info.cluster_id.unique())} clusters")
        print('\n\n\n')

        # Subselect clusters of interest
        df = df.loc[df['cluster_id'].isin(info.cluster_id.values)].copy()

        assert set(df.cluster_id) == set(info.cluster_id)

        dfs.append(df)
        info_dfs.append(info)

    data = pd.concat(dfs)
    cluster_info = pd.concat(info_dfs)

    off_dat = data[
        (data['state'] == 'off')
        & (data['condition'] != 'interbout')
    ]

    # Rename conditions
    for cond in off_dat.condition.unique():
        if 'baseline' in cond:
            off_dat.replace(cond, 'baseline', inplace=True)
        if 'recovery' in cond:
            off_dat.replace(cond, 'recovery', inplace=True)
    
    # Rename conditions
    for cond in data.condition.unique():
        if 'baseline' in cond:
            data.replace(cond, 'baseline', inplace=True)
        if 'recovery' in cond:
            data.replace(cond, 'recovery', inplace=True)

    return data, off_dat, cluster_info
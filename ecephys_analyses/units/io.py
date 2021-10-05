from pathlib import Path

import ecephys.units
from ecephys_analyses.data import channel_groups, paths


def get_sorting_extractor(
    subject, condition, sorting_condition,
    region='all',
    selection_intervals=None,
    good_only=False,
    root_key=None,
):
    """Return (<subsortingextractor>, <cluster_info>)"""
    # Params
    if selection_intervals is None:
        selection_intervals = {}
    print(f'Get sorting extractor, region={region}, selection_intervals={selection_intervals}, good_only={good_only}, root_key={root_key}')

    # Path 
    ks_dir = paths.get_datapath(
        subject,
        condition,
        sorting_condition,
        root_key=root_key,
    )

    # Get depth intervals either from file ('region') or from `selection_intervals` kwargs
    if region is None:
        assert 'depth' in selection_intervals.keys()
    if region is not None:
        assert 'depth' not in selection_intervals.keys()
        if region == 'all':
            depth_interval = (0.0, float('Inf'))
        else:
            depth_interval = channel_groups.region_depths[subject][condition][region]
        selection_intervals = {
            'depth': depth_interval,
            **selection_intervals
        }

    # Get clusters
    extr = ecephys.units.load_sorting_extractor(
        ks_dir,
        good_only=good_only,
        selection_intervals=selection_intervals,
    )
    info_all =  ecephys.units.get_cluster_info(ks_dir)
    info = info_all[info_all['cluster_id'].isin(extr.get_unit_ids())]

    return extr, info

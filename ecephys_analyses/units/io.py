from pathlib import Path

import ecephys.units
from ecephys_analyses.data import channel_groups, paths


def get_sorting_data(
    subject, condition, sorting_condition,
    region='all',
    selection_intervals=None,
    assign_regions=True,
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
    if region is None and 'depth' in selection_intervals.keys():
        pass
    else:
        if region is None or region == 'all':
            assert 'depth' not in selection_intervals.keys()
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
    info = info_all[info_all['cluster_id'].isin(extr.get_unit_ids())].copy()

    # Add boolean column for each region
    if assign_regions:
        regions = channel_groups.region_depths[subject][condition]
        for region, region_depths in regions.items():
            info[region] = info['depth'].between(*region_depths)

    return extr, info

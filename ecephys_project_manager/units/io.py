import ecephys.units
from ecephys_project_manager.pipe import get_sorting_output_path
from ..cluster_groups import get_cluster_group_dict
from ..depths import get_regions, get_depths


# TODO: Are these arguments truly all optional?
# TODO: The `analysis_name` parameter does not actually correspond to any other `analysis_name` parameters.
# Instead, it is a concatenation of several analyses: the sorting analysis name, the postprocessing analysis name, and the quality metrics analysis name.
# For example, `ks2_5_catgt_df_postpro_2_metrics_all_isi`.
# TODO: `region` loads only a single region, as specified in `depths.yaml`. This option should be removed, as it is probably better to provide this as an option in the selection_intervals dictionary.
# If it is going to stay, it should allow selection of more than one region. Also, it shouldn't allow both `None` and `all` to yield the same behavior.
def get_sorting_data(
    project=None,
    subject=None,
    experiment=None,
    alias=None,
    probe=None,
    analysis_name=None,
    region=None,
    selection_intervals=None,
    assign_regions=True,
    selected_groups=None,
    override_cluster_groups=False,
):
    """Return (<SpikeInterface.SubSortingExtractor>, <cluster_info>)."""

    assert all(
        [
            arg is not None
            for arg in [project, subject, experiment, alias, probe, analysis_name]
        ]
    )

    # Params
    if selection_intervals is None:
        selection_intervals = {}
    print(f"Get sorting extractor: {locals()}")

    # Path
    ks_dir = get_sorting_output_path(
        project=project,
        subject=subject,
        experiment=experiment,
        alias=alias,
        probe=probe,
        analysis_name=analysis_name,
    )

    # Get depth intervals either from file ('region') or from `selection_intervals` kwargs
    if region is None and "depth" in selection_intervals.keys():
        pass
    else:
        if region is None or region == "all":
            assert "depth" not in selection_intervals.keys()
            depth_interval = (0.0, float("Inf"))
        else:
            depth_interval = get_depths(subject, experiment, probe, region)
        selection_intervals = {"depth": depth_interval, **selection_intervals}

    # Get cluster group overrides
    if override_cluster_groups:
        cluster_group_overrides = get_cluster_group_dict(
            subject, experiment, alias, probe
        )
        print(f"cluster group overrides: {cluster_group_overrides}")
    else:
        cluster_group_overrides = None

    # Get clusters
    extr = ecephys.units.load_sorting_extractor(
        ks_dir,
        selected_groups=selected_groups,
        selection_intervals=selection_intervals,
        cluster_group_overrides=cluster_group_overrides,
    )
    info_all = ecephys.units.get_cluster_info(ks_dir)
    info = info_all[info_all["cluster_id"].isin(extr.get_unit_ids())].copy()

    # Add boolean column for each region
    if assign_regions:
        regions = get_regions(subject, experiment, probe)
        for region, region_depths in regions.items():
            info[region] = info["depth"].between(*region_depths)

    # TODO: Assert that info matches extr._properties before returning
    return extr, info

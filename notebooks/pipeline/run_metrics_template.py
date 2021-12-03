import ecephys_analyses.pipe
import itertools

"""Copy, modify and run to run the whole pipeline for several datasets."""

project = 'test_project'

subject_probe_list = [
    # ('CNPIX99-Miles', 'imec0'),
    # ('CNPIX99-Miles', 'imec1'),
    # ('CNPIX999-Mewtwo', 'imec1'),
]

experiment_alias_list = [
    # ('example_experiment', 'example_alias'),
    # ('example_experiment', 'example_alias_2'),
]

# Analyses ran in pipeline (pre-curation)
sorting_analysis_name = 'ks2_5_catgt_df'  # Must be in 'sorting' doc in analysis_cfg.yaml
postpro_analysis_name = 'postpro_2'  # Must be in 'ks_postprocessing' doc in analysis_cfg.yaml

# Post-curation
analysis_name = 'metrics_all_isi'

# Misc
rerun_existing = True
dry_run = False


if __name__ == '__main__':

    for (
        (subject, probe),
        (experiment, alias),
    ) in itertools.product(
        subject_probe_list,
        experiment_alias_list
    ):

        ecephys_analyses.pipe.run_postprocessing(
            project=project,
            subject=subject,
            experiment=experiment,
            alias=alias,
            probe=probe,
            analysis_name=analysis_name,
            sorting_analysis_name=f"{sorting_analysis_name}_{postpro_analysis_name}",
            rerun_existing=rerun_existing,
            dry_run=dry_run
        )
import ecephys_project_manager.pipe
import itertools

"""Copy, modify and run to run the whole pipeline for several datasets."""

project = 'my_project'
prepro_project = 'catgt'  # Only for (temporary) catGT data.

subject_probe_list = [
    # ('CNPIX99-Miles', 'imec0'),
    # ('CNPIX99-Miles', 'imec1'),
    # ('CNPIX999-Mewtwo', 'imec1'),
]

experiment_alias_list = [
    # ('example_experiment', 'example_alias'),
    # ('example_experiment', 'example_alias_2'),
]

# Analysis names
prepro_analysis_name = 'prepro_df'  # Must be in 'preprocessing' doc in analysis_cfg.yaml
sorting_analysis_name = 'ks2_5_catgt_df'  # Must be in 'sorting' doc in analysis_cfg.yaml
postpro_analysis_name = 'postpro_2'  # Must be in 'ks_postprocessing' doc in analysis_cfg.yaml

# Misc
clear_preprocessed_data = False  # Rm catGT data after sorting
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

        ecephys_project_manager.pipe.run_pipeline(
            project=project,
            prepro_project=prepro_project,
            subject=subject,
            experiment=experiment,
            alias=alias,
            probe=probe,
            prepro_analysis_name=prepro_analysis_name,
            sorting_analysis_name=sorting_analysis_name,
            postpro_analysis_name=postpro_analysis_name,
            clear_preprocessed_data=clear_preprocessed_data,
            rerun_existing=rerun_existing,
            dry_run=dry_run
        )
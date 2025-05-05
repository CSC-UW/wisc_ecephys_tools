from ecephys.wne.sglx.pipeline import consolidate_visbrain_hypnograms
from wisc_ecephys_tools import projects, subjects
from wisc_ecephys_tools.rats import utils


def do_experiment(experiment: str):
    """Process all subjects and experiments in the project."""
    all_ = utils.get_subject_experiment_probe_tuples(
        experiment_filter=lambda x: x == experiment
    )
    for subject, experiment, probe in all_:
        print(f"Doing {subject} {experiment} {probe}")
        consolidate_visbrain_hypnograms.do_experiment_probe(
            experiment,
            probe,
            subjects.get_sglx_subject(subject),
            projects.get_sglx_project("shared"),
            projects.get_sglx_project("shared"),
        )

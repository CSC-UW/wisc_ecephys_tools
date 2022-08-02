import os

PACKAGE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIRECTORY = os.path.join(PACKAGE_DIRECTORY, "config")
SUBJECTS_DIRECTORY = os.path.join(PACKAGE_DIRECTORY, "subjects")


def get_config_file(filename, config_dir=None):
    if config_dir is None:
        config_dir = CONFIG_DIRECTORY
    return os.path.join(config_dir, filename)


def get_subject_file(subject_name, subjects_dir=None):
    if subjects_dir is None:
        subjects_dir = SUBJECTS_DIRECTORY
    return os.path.join(subjects_dir, f"{subject_name}.yml")

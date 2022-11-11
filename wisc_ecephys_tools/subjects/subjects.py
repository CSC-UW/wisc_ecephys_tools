import os
from pathlib import Path

DEFAULT_SUBJECTS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def get_subjects_directory():
    return Path(DEFAULT_SUBJECTS_DIRECTORY)

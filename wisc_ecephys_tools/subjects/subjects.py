import os
from pathlib import Path
from ecephys import wne

DEFAULT_SUBJECTS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def get_subjects_directory():
    return Path(DEFAULT_SUBJECTS_DIRECTORY)


def get_wne_subject(subjectName):
    subjectsDir = get_subjects_directory()
    subjLib = wne.sglx.SGLXSubjectLibrary(subjectsDir)
    return subjLib.get_subject(subjectName)

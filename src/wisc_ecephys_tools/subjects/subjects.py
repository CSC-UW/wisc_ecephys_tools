import os
from pathlib import Path

from ecephys import wne

DEFAULT_SUBJECTS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def get_subjects_directory():
    return Path(DEFAULT_SUBJECTS_DIRECTORY)


def get_subject_library():
    subjectsDir = get_subjects_directory()
    return wne.sglx.SGLXSubjectLibrary(subjectsDir)


def get_sglx_subject(subjectName):
    subjLib = get_subject_library()
    return subjLib.get_subject(subjectName)

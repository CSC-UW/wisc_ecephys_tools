import os
from pathlib import Path

from ecephys import wne

DEFAULT_SUBJECTS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Module-level cache for the subject library
_cached_library = None


def get_subjects_directory():
    return Path(DEFAULT_SUBJECTS_DIRECTORY)


def get_subject_library(force_refresh=False):
    """Get the SGLXSubjectLibrary, using an in-memory cache.

    Args:
        force_refresh: If True, bypass the cache and create a new library instance,
                      reading from the parquet file on disk. Default is False.

    Returns:
        SGLXSubjectLibrary instance

    Example:
        lib = get_subject_library()
        new = lib.refresh_cache()
        new.write_cache() # Persist the new cache.
        lib = get_subject_library() # The old cache is still used.
        lib = get_subject_library(force_refresh=True) # Now the new cache is used.
    """
    global _cached_library
    if _cached_library is None or force_refresh:
        subjectsDir = get_subjects_directory()
        _cached_library = wne.sglx.SGLXSubjectLibrary(subjectsDir)
    return _cached_library


def get_sglx_subject(subjectName):
    subjLib = get_subject_library()
    return subjLib.get_subject(subjectName)

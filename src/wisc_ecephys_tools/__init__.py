# Only import lightweight modules at package level.
# ephyviewer_app and rats must be imported directly to avoid slow import times
# from GUI libraries and brainglobe:
#   from wisc_ecephys_tools import ephyviewer_app
#   from wisc_ecephys_tools import rats
from . import constants, core
from .projects import get_sglx_project, get_wne_project
from .subjects import get_sglx_subject, get_subjects_directory

__all__ = [
    "constants",
    "core",
    "get_sglx_project",
    "get_wne_project",
    "get_sglx_subject",
    "get_subjects_directory",
]

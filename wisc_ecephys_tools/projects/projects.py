"""
Experiments + aliases assumed, sessions not?
Only projects.yaml is required to resolve paths?

- project_dir/ (e.g. SPWRs/)
  - subject_dir/ (e.g. ANPIX11-Adrian/)
  - experiment_dir/ (e.g. novel_objects_deprivation/)
    - alias_dir/ (e.g. recovery_sleep/)
      - alias_subject_dir/ (e.g. ANPIX11-Adrian/)
    - subalias_dir/ (e.g. sleep_homeostasis_0/, sleep_homeostasis_1/) <- Only if there is N>1 subaliases
      - subalias_subject_dir/ (e.g. ANPIX11-Adrian/)
    - experiment_subject_dir/ (e.g. ANPIX11-Adrian/)

"""
import os
from pathlib import Path

from ecephys import wne

# You could name a project the same thing as an experiment
# You could name a project "Common" or "Scoring" or "Sorting"

DEFAULT_PROJECTS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROJECTS_FILENAME = "projects.yaml"


def get_projects_file(
    filename=DEFAULT_PROJECTS_FILENAME, projects_dir=DEFAULT_PROJECTS_DIRECTORY
):
    return Path(os.path.join(projects_dir, filename))


def get_wne_project(
    project_name,
    filename=DEFAULT_PROJECTS_FILENAME,
    projects_dir=DEFAULT_PROJECTS_DIRECTORY,
):
    projects_file = get_projects_file(filename=filename, projects_dir=projects_dir)
    projects_library = wne.ProjectLibrary(projects_file)
    return projects_library.get_project(project_name=project_name)

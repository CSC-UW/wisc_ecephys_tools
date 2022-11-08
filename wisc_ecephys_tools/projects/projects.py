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
import yaml
from pathlib import Path

# You could name a project the same thing as an experiment
# You could name a project "Common" or "Scoring" or "Sorting"

DEFAULT_PROJECTS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def get_projects_file(
    filename="projects.yaml", projects_dir=DEFAULT_PROJECTS_DIRECTORY
):
    return Path(os.path.join(projects_dir, filename))
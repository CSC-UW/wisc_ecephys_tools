"""
- project_dir/ (e.g. SPWRs/)
  - subject_dir/ (e.g. ANPIX11-Adrian/)
  - experiment_dir/ (e.g. novel_objects_deprivation/)
    - alias_dir/ (e.g. recovery_sleep/)
      - alias_subject_dir/ (e.g. ANPIX11-Adrian/)
    - subalias_dir/ (e.g. sleep_homeostasis_0/, sleep_homeostasis_1/) <- Only if there is N>1 subaliases
      - subalias_subject_dir/ (e.g. ANPIX11-Adrian/)
    - experiment_subject_dir/ (e.g. ANPIX11-Adrian/)

You could name a project the same thing as an experiment, if you wanted to.
"""

import os
from functools import lru_cache
from pathlib import Path

from ecephys import wne
from ecephys.wne import sglx


# TODO: Use importlib.resources and make YAML files hatch build artifacts.
def get_projects_file() -> Path:
    return Path(os.path.dirname(os.path.abspath(__file__))) / "projects.yaml"


@lru_cache(maxsize=8)
def get_sglx_project_library(projects_file: str) -> sglx.SGLXProjectLibrary:
    # Assert type to avoid cache misses from equivalent but differently-typed paths
    assert isinstance(projects_file, str), (
        f"projects_file must be str, got {type(projects_file)}"
    )
    return sglx.SGLXProjectLibrary(projects_file)


@lru_cache(maxsize=8)
def get_wne_project_library(projects_file: str) -> wne.ProjectLibrary:
    # Assert type to avoid cache misses from equivalent but differently-typed paths
    assert isinstance(projects_file, str), (
        f"projects_file must be str, got {type(projects_file)}"
    )
    return wne.ProjectLibrary(projects_file)


def get_sglx_project(project_name: str) -> sglx.SGLXProject:
    lib = get_sglx_project_library(str(get_projects_file()))
    return lib.get_project(project_name=project_name)


def get_wne_project(project_name: str) -> wne.Project:
    lib = get_wne_project_library(str(get_projects_file()))
    return lib.get_project(project_name=project_name)

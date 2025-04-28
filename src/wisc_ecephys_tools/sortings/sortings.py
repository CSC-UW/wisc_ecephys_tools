from pathlib import Path
from typing import Union

from brainglobe_atlasapi import BrainGlobeAtlas

import wisc_ecephys_tools.projects as projects
from ecephys.utils import read_htsv

SHARED_PROJECT_NAME = "shared"
PROJ = projects.get_wne_project(SHARED_PROJECT_NAME)
BRAINGLOBE_DIR = PROJ.get_project_directory() / ".brainglobe"
DF_ATLAS = "whs_sd_rat_39um"

DF_EXCLUDE_DESCENDANTS_OF = ["V", "wmt"]

Pathlike = Union[Path, str]


def get_atlas(atlas_name: str = DF_ATLAS, brainglobe_dir: Pathlike = BRAINGLOBE_DIR):
    return BrainGlobeAtlas(atlas_name, brainglobe_dir=brainglobe_dir)


def get_subject_probe_list(
    experiment: str, alias: str, require_hypnogram_and_anatomy: bool = True
) -> list[tuple[str, str]]:
    """Return [(<subj>, <prb>)] list of sortings.

    If `require_hypnogram_and_anatomy` is True (default), then the experiment-subject
    directory wll be checked, and only subjects with a hypnogram and probes with anatomy
    will be included.

    As of 4/28/2025, sortings have only been done for `novel_objects_deprivation`
    experiments and `full` aliases.
    """

    # Get the available sortings
    s3 = projects.get_wne_project("shared")

    sortings_dir = s3.get_alias_directory(experiment, alias)

    available_sortings = {
        subj.name: [
            x.name.removeprefix("sorting.") for x in sorted(subj.glob("sorting.imec*"))
        ]
        for subj in sortings_dir.iterdir()
        if subj.is_dir()
    }  # e.g. {'CNPIX4-Doppio': ['imec0', 'imec1], 'CNPIX9-Luigi: ['imec0], ...}

    available_subject_probes = []
    for subj, prbs in available_sortings.items():
        available_subject_probes += [(subj, prb) for prb in prbs]

    if not require_hypnogram_and_anatomy:
        return available_subject_probes

    # Collect info about the various sortings, for display, and for determing parameters to use when loading
    has_hypnogram = {
        subject: s3.get_experiment_subject_file(
            experiment, subject, "hypnogram.htsv"
        ).exists()
        for subject in available_sortings
    }  # TODO: This should just be checked in the load_multiprobe_sorting function.... TB: Yes but it would require (slowish) loading of all sortings

    has_anatomy = {
        subject: {
            probe: s3.get_experiment_subject_file(
                experiment, subject, f"{probe}.structures.htsv"
            ).exists()
            for probe in probes
        }
        for subject, probes in available_sortings.items()
    }  # TODO: This should just be checked in the load_multiprobe_sorting function.... TB: Yes but it would require (slowish) loading of all sortings

    subject_probes_with_hypnogram_and_anatomy = [
        (subj, prb)
        for subj, prb in available_subject_probes
        if has_hypnogram[subj] and has_anatomy[subj][prb]
    ]

    return subject_probes_with_hypnogram_and_anatomy


def get_subject_probe_structure_list(
    experiment: str,
    alias: str,
    select_descendants_of: list[str] = None,
    exclude_descendants_of: list[str] = DF_EXCLUDE_DESCENDANTS_OF,
    atlas: BrainGlobeAtlas = None,
) -> list[tuple[str, str, str]]:
    """Return [(<subj>, <prb>, <acronym>)] list of structures of interest."""

    if atlas is None:
        atlas = get_atlas()

    if select_descendants_of is not None:
        unrecognized = [
            a for a in select_descendants_of if a not in atlas.lookup_df.acronym.values
        ]
        if any(unrecognized):
            raise ValueError(
                f"Unrecognized acronyms in `select_descendants_of` kwarg: {unrecognized}.\n"
                f"Available acronyms: {sorted(atlas.lookup_df.acronym.values)}"
            )
    if exclude_descendants_of is not None:
        unrecognized = [
            a for a in exclude_descendants_of if a not in atlas.lookup_df.acronym.values
        ]
        if any(unrecognized):
            raise ValueError(
                f"Unrecognized acronyms in `exclude_descendants_of` kwarg: {unrecognized}.\n"
                f"Available acronyms: {sorted(atlas.lookup_df.acronym.values)}"
            )

    # Get the available sortings

    completed_subject_probes = get_subject_probe_list(
        experiment,
        alias,
        require_hypnogram_and_anatomy=True,
    )

    completed_subject_probe_structures = []
    unrecognized_structs = []
    for subj, prb in completed_subject_probes:
        struct = read_htsv(
            s3.get_experiment_subject_file(experiment, subj, f"{prb}.structures.htsv")
        )
        for acronym in struct.acronym.unique():
            if acronym not in atlas.lookup_df.acronym.values:
                unrecognized_structs.append(acronym)
                continue
            ancestors = atlas.get_structure_ancestors(acronym)
            if exclude_descendants_of is not None:
                if acronym in exclude_descendants_of or any(
                    [exclude in ancestors for exclude in exclude_descendants_of]
                ):
                    continue
            if select_descendants_of is not None:
                if acronym not in select_descendants_of and not any(
                    [select in ancestors for select in select_descendants_of]
                ):
                    continue
            completed_subject_probe_structures.append((subj, prb, acronym))

    if unrecognized_structs:
        import warnings

        warnings.warn(
            f"The following structures were unrecognized and ignored across all datasets: {unrecognized_structs}"
        )

    return completed_subject_probe_structures

import warnings

from brainglobe_atlasapi import BrainGlobeAtlas

import ecephys.utils
from wisc_ecephys_tools import projects
from wisc_ecephys_tools.rats import constants, utils


# TODO: This exists basically for backwards compatibility. This kind of logic should
# probably be handled on a project-by-project basis.
# TODO: experiment and alias shouldn't even be accepted as arguments, or should be
# optional.
def get_subject_probe_list(
    experiment: str, alias: str, require_hypnogram_and_anatomy: bool = True
) -> list[tuple[str, str]]:
    assert (
        experiment == constants.SleepDeprivationExperiments.NOD and alias == "full"
    ), "As of 6/23/2025, sortings have only been done for full alias of NOD."
    s3 = projects.get_wne_project("shared")

    def _keep(subject: str, experiment: str, probe: str) -> bool:
        keep = utils.has_sorting(subject, experiment, probe, s3)
        if require_hypnogram_and_anatomy:
            keep = (
                keep
                and utils.has_anatomy(subject, experiment, probe, s3)
                and utils.has_hypnogram(
                    subject, experiment, None, s3
                )  # TODO: This should check for probe-specific hypnogram
            )
        return keep

    sep = utils.get_subject_experiment_probe_tuples(
        experiment_filter=lambda x: x == experiment
    )
    lst = [(s, p) for s, e, p in sep if _keep(s, e, p)]
    return lst


# TODO: This exists basically for backwards compatibility. This kind of logic should
# probably be handled on a project-by-project basis.
# TODO: experiment and alias shouldn't even be accepted as arguments, or should be
# optional.
# TODO: Ignoring unrecognized structures should probably be an option.
def get_subject_probe_structure_list(
    experiment: str,
    alias: str,
    select_descendants_of: list[str] = None,
    exclude_descendants_of: list[str] = ["V", "wmt"],
    atlas: BrainGlobeAtlas = None,
) -> list[tuple[str, str, str]]:
    """Return [(<subj>, <prb>, <acronym>)] list of structures of interest.

    WARNING: This has to be used with extreme caution! For example, "CA3" and "SUB" are
    descendants of "Cx"! But setting `exclude_descendants_of=["HF"]` won't exclude
    descendants of "V" and "wmt"! TODO: Improve.
    """

    if atlas is None:
        atlas = BrainGlobeAtlas("whs_sd_rat_39um")

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
    )  # TODO: We should not require the hypnogram for any of this.

    completed_subject_probe_structures = []
    unrecognized_structs = []
    for subj, prb in completed_subject_probes:
        struct = ecephys.utils.read_htsv(
            projects.get_wne_project("shared").get_experiment_subject_file(
                experiment, subj, f"{prb}.structures.htsv"
            )
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
        unrecognized_structs = set(unrecognized_structs)
        warnings.warn(
            f"The following structures were unrecognized and ignored across all datasets: {unrecognized_structs}"
        )

    return completed_subject_probe_structures

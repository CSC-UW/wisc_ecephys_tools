import re

from ecephys import wne
from wisc_ecephys_tools import projects, subjects
from wisc_ecephys_tools.rats.constants import SleepDeprivationExperiments


def is_valid_cnpix_subject_name(subject: str) -> bool:
    """
    is_cnpix_subject("CNPIX2-Segundo") -> True
    is_cnpix_subject("CNPIX12-Santiago") -> True
    is_cnpix_subject("ANPIX1-Sputnik") -> False
    """
    return bool(re.match(r"^CNPIX[1-9]\d*-\w+$", subject))


def get_subject_experiment_probe_tuples(
    experiment_filter: callable = None, expand_probes: bool = True
) -> list[tuple[str, str, str]]:
    lib = subjects.get_subject_library()
    return lib.get_subject_experiment_probe_tuples(
        subject_filter=is_valid_cnpix_subject_name,
        experiment_filter=experiment_filter,
        expand_probes=expand_probes,
    )


# The functions below here are not really rat-specific.
# They are only used for rat data, but could in principle be used for other data,
# such as acute mouse neuropixel data.
# --------------------------------------------------------------------------------------


def _red(text):
    return f"\033[91m{text}\033[0m"


def _green(text):
    return f"\033[92m{text}\033[0m"


def has_bad_channels_marked(
    subject: str,
    experiment: str,
    probe: str,
    params_project: wne.sglx.SGLXProject = projects.get_sglx_project("shared"),
    verbose: bool = False,
) -> bool:
    params = params_project.load_experiment_subject_params(experiment, subject)
    try:
        bad_channels = params["probes"][probe]["badChannels"]
        if verbose:
            print(
                _green(
                    f"{subject}, {experiment}, {probe}: Bad channels: {bad_channels}"
                )
            )
        return True
    except KeyError:
        if verbose:
            print(_red(f"{subject}, {experiment}, {probe}: Bad channels not marked."))
        return False


def has_lfps(
    subject: str,
    experiment: str,
    probe: str,
    lf_project: wne.sglx.SGLXProject = projects.get_sglx_project("shared_nobak"),
    verbose: bool = False,
) -> bool:
    lf_file = lf_project.get_experiment_subject_file(
        experiment, subject, f"{probe}{wne.constants.FileExtensions.LFP}"
    )
    if lf_file.exists():
        if verbose:
            print(_green(f"{subject}, {experiment}, {probe}: LFPs found"))
        return True
    else:
        if verbose:
            print(_red(f"{subject}, {experiment}, {probe}: No LFPs found"))
        return False


def has_hypnogram(
    subject: str,
    experiment: str,
    probe: str | None = None,
    hg_project: wne.sglx.SGLXProject = projects.get_sglx_project("shared"),
    verbose: bool = False,
) -> bool:
    if probe is None:
        hg_file = hg_project.get_experiment_subject_file(
            experiment, subject, f"{wne.constants.Files.HYPNOGRAM}"
        )
    else:
        hg_file = hg_project.get_experiment_subject_file(
            experiment, subject, f"{probe}{wne.constants.FileExtensions.HYPNOGRAM}"
        )
    if hg_file.exists():
        if verbose:
            print(_green(f"{subject}, {experiment}, {probe}: Hypnogram found"))
        return True
    else:
        if verbose:
            print(_red(f"{subject}, {experiment}, {probe}: No hypnogram found"))
        return False


def has_anatomy(
    subject: str,
    experiment: str,
    probe: str,
    project: wne.sglx.SGLXProject = projects.get_sglx_project("shared"),
    verbose: bool = False,
) -> bool:
    anat_file = project.get_experiment_subject_file(
        experiment, subject, f"{probe}{wne.constants.FileExtensions.STRUCTURES}"
    )
    if anat_file.exists():
        if verbose:
            print(_green(f"{subject}, {experiment}, {probe}: Anatomy found"))
        return True
    else:
        if verbose:
            print(_red(f"{subject}, {experiment}, {probe}: No anatomy found"))
        return False


def has_sorting(
    subject: str,
    experiment: str,
    probe: str,
    sorting_project: wne.sglx.SGLXProject = projects.get_sglx_project("shared"),
    verbose: bool = False,
) -> bool:
    assert experiment == SleepDeprivationExperiments.NOD, (
        "As of 6/23/2025, sortings have only been done for full alias of NOD."
    )
    subject_sorting_dir = sorting_project.get_alias_subject_directory(
        experiment, "full", subject
    )
    probe_sorting_dir = subject_sorting_dir / f"sorting.{probe}"
    if probe_sorting_dir.exists():
        if verbose:
            print(_green(f"{subject}, {experiment}, {probe}: Sorting found"))
        return True
    else:
        if verbose:
            print(_red(f"{subject}, {experiment}, {probe}: No sorting found"))
        return False

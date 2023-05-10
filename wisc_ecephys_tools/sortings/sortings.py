import wisc_ecephys_tools as wet


def get_completed_subject_probes(experiment, alias):
    """Return list of (<subj>, <prb>) for sortings with everything"""

    # Get the available sortings
    ss = wet.get_wne_project("shared_sortings")
    s3 = wet.get_wne_project("shared_s3")

    sortings_dir = ss.get_alias_directory(experiment, alias)

    available_sortings = {
        subj.name: [
            x.name.removeprefix("sorting.") for x in sorted(subj.glob("sorting.imec*"))
        ]
        for subj in sortings_dir.iterdir()
        if subj.is_dir()
    }  # e.g. {'CNPIX4-Doppio': ['imec0', 'imec1], 'CNPIX9-Luigi: ['imec0], ...}

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

    available_subject_probes = []
    for subj, prbs in available_sortings.items():
        available_subject_probes += [(subj, prb) for prb in prbs]

    completed_subject_probes = [
        (subj, prb) for subj, prb in available_subject_probes
        if has_hypnogram[subj]
        and has_anatomy[subj]
    ]

    return completed_subject_probes
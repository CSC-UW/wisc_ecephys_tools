import wisc_ecephys_tools as wet
from ecephys import wne
from findlay2025a import core
from wisc_ecephys_tools.rats import hypnograms


def get_statistical_condition_hypnograms(subject: str, experiment: str, probe: str):
    raise NotImplementedError("This function is not yet implemented.")
    s3 = wet.get_sglx_project("shared")

    lbrl_hg = wet.rats.scoring.load_hypnogram(
        s3,
        experiment,
        subject,
        probe,
        include_ephyviewer_edits=True,
        include_sorting_nodata=False,
        include_lf_consolidated_artifacts=False,
        include_ap_consolidated_artifacts=False,
        include_lf_sglx_filetable_nodata=False,
        include_ap_sglx_filetable_nodata=False,
        simplify=True,
        fallback=True,
    )

    # Load a more conservative hypnogram with artifacts and such that we might want to know about.
    cons_hg = wet.rats.scoring.load_hypnogram(
        s3,
        experiment,
        subject,
        probe,
        include_ephyviewer_edits=True,
        include_sorting_nodata=True,
        include_lf_consolidated_artifacts=True,
        include_ap_consolidated_artifacts=True,
        include_lf_sglx_filetable_nodata=True,
        include_ap_sglx_filetable_nodata=True,
        simplify=True,
        fallback=True,
    )
    # If you wanted probe-agnostic statistical_condition_hypnograms,
    # I guess you would take periods where all probes' conservative
    # hypnograms agree, leave those intact, and "None"-ify where they
    # disagree, then use this new hypnogram as the conservative hypnogram.
    # It won't be maximally accurate, but at least it will be consistent...
    # You could do the same for the liberal hypnogram.
    return hypnograms.compute_statistical_condition_hypnograms(
        lbrl_hg, cons_hg, experiment, subject
    )


def do_experiment(sglx_subject: wne.sglx.SGLXSubject, experiment: str):
    raise NotImplementedError("This function is not yet implemented.")
    nb = core.get_project("seahorse")
    sc_hgs = get_statistical_condition_hypnograms(sglx_subject, experiment)

    for c, c_hg in sc_hgs.items():
        c_hg.write_htsv(
            nb.get_experiment_subject_file(
                experiment, sglx_subject.name, f"{c}_hypnogram.htsv"
            )  # TODO: Should save probe name too.
        )


def do_project():
    raise NotImplementedError("This function is not yet implemented.")
    for sglx_subject, experiment in core.yield_sglx_subject_experiment_pairs():
        print(f"Processing {sglx_subject.name} {experiment}")
        do_experiment(sglx_subject, experiment)

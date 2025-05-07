import pandas as pd

import ecephys.hypnogram as hyp
import wisc_ecephys_tools as wet
from ecephys import wne
from wisc_ecephys_tools.rats import cnd_hgs, exp_hgs

EXTENDED_WAKE_KWARGS = {
    "minimum_endpoint_bout_duration": 120,
    "maximum_antistate_bout_duration": 95,
    "minimum_fraction_of_final_match": 0.95,
}
CIRCADIAN_MATCH_TOLERANCE = 30 * 60  # 30 minutes


# If you wanted probe-agnostic statistical_condition_hypnograms,
# I guess you would take periods where all probes' conservative
# hypnograms agree, leave those intact, and "None"-ify where they
# disagree, then use this new hypnogram as the conservative hypnogram.
# It won't be maximally accurate, but at least it will be consistent...
# You could do the same for the liberal hypnogram.
# You could also just compute the statistical condition hypnograms
# in a probe-specific manner, then hope to reconcile the outputs.
# That's probably safer, because it'll be easier to see precisely
# where the discrepancies are.
# Hold off on implementing either for now. It may not be necessary.
def do_probe(
    subject: wne.sglx.SGLXSubject, experiment: str, probe: str
) -> dict[str, hyp.FloatHypnogram]:
    s3 = wet.get_sglx_project("shared")

    lbrl_hg = exp_hgs.get_liberal_hypnogram(
        s3,
        experiment,
        subject,
        probe,
    )

    cons_hg = exp_hgs.get_conservative_hypnogram(
        s3,
        experiment,
        subject,
        probe,
    )

    return cnd_hgs.compute_statistical_condition_hypnograms(
        lbrl_hg,
        cons_hg,
        experiment,
        subject,
        extended_wake_kwargs=EXTENDED_WAKE_KWARGS,
        circadian_match_tolerance=CIRCADIAN_MATCH_TOLERANCE,
    )


def do_experiment(
    sglx_subject: wne.sglx.SGLXSubject,
    experiment: str,
    probes: list[str] | None = None,
    verbose: bool = False,
    save: bool = False,
) -> tuple[
    dict[str, hyp.FloatHypnogram],
    pd.DataFrame,
    dict[str, dict[str, hyp.FloatHypnogram]],
]:
    probes = probes or sglx_subject.get_experiment_probes(experiment)
    prb_hgs = {prb: do_probe(sglx_subject, experiment, prb) for prb in probes}
    if save:
        s3 = wet.get_sglx_project("shared")
        for prb, hgs in prb_hgs.items():
            fpath = s3.get_experiment_subject_file(
                experiment,
                sglx_subject.name,
                f"{prb}.condition_hypnograms.parquet",
            )
            cnd_hgs.save_statistical_condition_hypnograms(hgs, fpath)
    if len(prb_hgs) < 2:
        return None, None, prb_hgs

    consensus_hgs, consensus_df = cnd_hgs.get_consensus(prb_hgs)
    if verbose:
        pd.set_option("display.max_rows", 100)
        print(consensus_df)
        pd.reset_option("display.max_rows")
    if save:
        fpath = s3.get_experiment_subject_file(
            experiment,
            sglx_subject.name,
            "consensus_condition_hypnograms.parquet",
        )
        cnd_hgs.save_statistical_condition_hypnograms(consensus_hgs, fpath)
    return consensus_hgs, consensus_df, prb_hgs

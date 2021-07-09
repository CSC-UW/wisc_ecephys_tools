import pandas as pd
from hypnogram import load_datetime_hypnogram
from ..paths import get_sglx_style_datapaths

SLEEP_HOMEOSTASIS = "sleep-homeostasis"


def load_hypnogram(subject, experiment, condition):
    hypnogram_paths = get_sglx_style_datapaths(
        subject=subject, experiment=experiment, condition=condition, ext="hypnogram.tsv"
    )
    hypnograms = [load_datetime_hypnogram(path) for path in hypnogram_paths]
    return pd.concat(hypnograms).reset_index(drop=True)


def load_sleep_homeostasis_hypnogram(
    subject,
    condition,
    keep_states=None,
    keep_between=None,
    keep_first=None,
    keep_last=None,
):
    assert not (
        keep_first and keep_last
    ), "Only one of keep_first or keep_last can be provided."
    hyp = load_hypnogram(subject, SLEEP_HOMEOSTASIS, condition)
    hyp = hyp.keep_states(keep_states) if keep_states else hyp
    hyp = hyp.keep_between(*keep_between) if keep_between else hyp
    hyp = hyp.keep_first(keep_first) if keep_first else hyp
    hyp = hyp.keep_last(keep_last) if keep_last else hyp
    return hyp
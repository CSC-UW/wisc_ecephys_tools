import pandas as pd
from ast import literal_eval


def load_sr_chans(path):
    df = pd.read_csv(path)
    df.sr_chans = df.sr_chans.apply(
        lambda x: [] if pd.isnull(x) else list(literal_eval(x))
    )

    return df

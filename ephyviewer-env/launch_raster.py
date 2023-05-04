import pathlib
import sys
import tkinter as tk
import ephyviewer
import xarray as xr
import numpy as np

import rich

from ecephys.wne.utils import load_singleprobe_sorting
import wisc_ecephys_tools as wet
from ecephys.units.ephyviewerutils import add_traceviewer_to_window

experiment = "novel_objects_deprivation"
alias = "full"


# Get the available sortings
ss = wet.get_wne_project("shared_sortings")
s3 = wet.get_wne_project("shared_s3")
slfp = wet.get_wne_project("seahorse")
chronic_sortings_dir = ss.get_alias_directory(experiment, alias)
available_sortings = {
    subj.name: [
        x.name.removeprefix("sorting.") for x in sorted(subj.glob("sorting.imec*"))
    ]
    for subj in chronic_sortings_dir.iterdir()
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
has_scoring_sigs = {
    subject: all(
        [
            slfp.get_experiment_subject_file(experiment, subject, fname).exists()
            for fname in ["scoring_lfp.zarr", "scoring_emg.zarr"]
        ]
    )
    for subject in available_sortings
}  # TODO: This should just be checked in the load_multiprobe_sorting function.... TB: Yes but it would require (slowish) loading of all sortings
sortings_summary = {
    subject: {
        "probes": available_sortings[subject],
        "anatomy": has_anatomy[subject],
        "hypnogram": has_hypnogram[subject],
        "scoring_sigs": has_scoring_sigs[subject],
    }
    for subject in available_sortings
}

# Simple GUI dialog for getting the desired probe
root = tk.Tk()
tk.Label(root, text="Available sortings").pack()
txt = tk.Text(root)
txt.insert(tk.END, rich.pretty.pretty_repr(sortings_summary))
txt.pack(anchor="w")
v = tk.IntVar()
available_subject_probes = [(None, None)]
for subj, prbs in available_sortings.items():
    available_subject_probes += [(subj, prb) for prb in prbs]
for i, (subj, prb) in enumerate(available_subject_probes):
    tk.Radiobutton(root, text=f"{subj}, {prb}", variable=v, value=i).pack(anchor="w")
tk.Button(text="Submit", command=root.destroy).pack()
root.mainloop()
subj_prb_i = v.get()
if subj_prb_i == 0:  # If window was closed without making a selection
    sys.exit()
subject, probe = available_subject_probes[subj_prb_i]
print(f"\nLoading: {subject}, {probe}\n")

# Load the sorting
wneSubject = wet.get_wne_subject(subject)
sorting = "sorting"
postprocessing = "postpro"
filters = {
    "quality": {
        "good",
        "mua",
    },  # "quality" property is "group" from phy curation. Remove noise
    "firing_rate": (0.0, float("Inf")),
    # ...
}

wneHypnogramProject = s3 if has_hypnogram[subject] else None
wneAnatomyProject = s3 if has_anatomy[subject][probe] else None
singleprobe_sorting = load_singleprobe_sorting(
    ss,
    wneSubject,
    experiment,
    alias,
    probe,
    sorting=sorting,
    postprocessing=postprocessing,
    wneAnatomyProject=wneAnatomyProject,
    wneHypnogramProject=wneHypnogramProject,
)
singleprobe_sorting = singleprobe_sorting.refine_clusters(
    filters,
    include_nans=True,
)


app = ephyviewer.mkQApp()
window = ephyviewer.MainViewer(
    debug=True, show_auto_scale=False, global_xsize_zoom=True
)

window = singleprobe_sorting.add_ephyviewer_hypnogram_view(window)

if has_scoring_sigs[subject]:
    print("Loading scoring signals")
    lfp = xr.open_dataarray(
        slfp.get_experiment_subject_file(experiment, subject, "scoring_lfp.zarr"),
        engine="zarr",
    )
    emg = xr.open_dataarray(
        slfp.get_experiment_subject_file(experiment, subject, "scoring_emg.zarr"),
        engine="zarr",
    )

    # Add EMG and LFP separately to avoid messy scaling
    tdiff = lfp.time.values[1] - lfp.time.values[0]
    srate = 1 / tdiff
    t_start = lfp.time.values[0]
    channel_names = lfp.signal.data
    view_params = {
        "display_labels": True,
        "scale_mode": "same_for_all",
    }
    window = add_traceviewer_to_window(
        window,
        lfp.data,
        1 / tdiff,
        t_start,
        channel_names=lfp.signal.data,
        view_name="Scoring LFP",
        view_params=view_params,
    )

    tdiff = emg.time.values[1] - emg.time.values[0]
    srate = 1 / tdiff
    t_start = emg.time.values[0]
    view_params = {
        "display_labels": True,
        "ylim_min": -0.05,
        "ylim_max": 0.8,
        # "scale_mode": "real_scale",
    }
    window = add_traceviewer_to_window(
        window,
        emg.data,
        1 / tdiff,
        t_start,
        channel_names=emg.signal.data,
        view_name="derived EMG",
        view_params=view_params,
    )

window = singleprobe_sorting.add_ephyviewer_spiketrain_views(
    window,
    by="depth",
    tgt_struct_acronyms=None,
    group_by_structure=True,
)

window.show()
app.exec()

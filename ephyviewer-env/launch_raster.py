import sys
import tkinter as tk

from ecephys import wne
from ecephys import units
import ephyviewer
import numpy as np
import pandas as pd
import rich
import wisc_ecephys_tools as wet
import xarray as xr

experiment = "novel_objects_deprivation"
alias = "full"


# Get the available sortings
ss = wet.get_sglx_project("shared_sortings")
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
off_fname_glob = f"*global_offs_*"
has_off_df = {
    subject: {
        probe: len(
            list(
                (
                    s3.get_experiment_subject_directory(experiment, subject) / "offs"
                ).glob(f"{probe}{off_fname_glob}")
            )
        )
        > 0
        for probe in probes
    }
    for subject, probes in available_sortings.items()
}  # TODO: This should just be checked in the load_multiprobe_sorting function.... TB: Yes but it would require (slowish) loading of all sortings
spatial_off_fname_glob = f"*spatial_offs_*"
has_spatial_off_df = {
    subject: {
        probe: len(
            list(
                (
                    s3.get_experiment_subject_directory(experiment, subject) / "offs"
                ).glob(f"{probe}{spatial_off_fname_glob}")
            )
        )
        > 0
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
has_sharp_wave_ripples = {
    subject: (
        slfp.get_experiment_subject_file(experiment, subject, "spws.pqt").exists()
        and slfp.get_experiment_subject_file(
            experiment, subject, "ripples.pqt"
        ).exists()
    )
    for subject in available_sortings
}

sortings_summary = {
    subject: {
        "probes": available_sortings[subject],
        "anatomy": has_anatomy[subject],
        "hypnogram": has_hypnogram[subject],
        "scoring_sigs": has_scoring_sigs[subject],
        "global offs": has_off_df[subject],
        "spatial offs": has_spatial_off_df[subject],
        "spwrs": has_sharp_wave_ripples[subject],
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
sglxSubject = wet.get_sglx_subject(subject)
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

if has_hypnogram[subject]:
    wneHypnogramProject = s3 if has_hypnogram[subject] else None
    hg = wneHypnogramProject.load_float_hypnogram(
        experiment, sglxSubject.name, simplify=True
    )
wneAnatomyProject = s3 if has_anatomy[subject][probe] else None
singleprobe_sorting = wne.sglx.utils.load_singleprobe_sorting(
    ss,
    sglxSubject,
    experiment,
    alias,
    probe,
    sorting=sorting,
    postprocessing=postprocessing,
    wneAnatomyProject=wneAnatomyProject,
)
singleprobe_sorting = singleprobe_sorting.refine_clusters(
    filters,
    include_nans=True,
)


has_off = has_off_df[subject][probe]
has_spatial_off = has_spatial_off_df[subject][probe]
has_hypno = has_hypnogram[subject]
has_scorsig = has_scoring_sigs[subject]
has_spwrs = has_sharp_wave_ripples[subject]

# GUI to select views to load
window = tk.Tk()
window.title("Select views to load.")
if has_hypno:
    var_hypno = tk.BooleanVar()
    checkbox = tk.Checkbutton(window, text="Display hypnogram", variable=var_hypno)
    checkbox.pack()
    checkbox.select()
if has_scorsig:
    var_scorsig = tk.BooleanVar()
    checkbox = tk.Checkbutton(
        window, text="Display scoring signals", variable=var_scorsig
    )
    checkbox.pack()
if has_off:
    # One checkbox per off_fname_suffix
    # Glob "<prb>.<acronym>.global_offs_<suffix>" and extract suffix
    off_fname_suffixes = np.unique(
        [
            ".".join(fpath.name.split(".")[2:])
            # fname
            for fpath in (
                s3.get_experiment_subject_directory(experiment, subject) / "offs"
            ).glob(f"{probe}*global_offs*")
        ]
    )  # Nasty sh*t good luck lol
    global_off_vars = {}
    for suffix in off_fname_suffixes:
        var_off = tk.BooleanVar()
        checkbox = tk.Checkbutton(
            window, text=f"Display global offs: {suffix}", variable=var_off
        )
        if suffix == wne.DF_OFF_FNAME_SUFFIX:
            checkbox.select()
        checkbox.pack()
        global_off_vars[suffix] = var_off
if has_spatial_off:
    # One checkbox per off_fname_suffix
    # Glob "<prb>.<acronym>.spatial_offs_<suffix>" and extract suffix
    spatial_off_fname_suffixes = np.unique(
        [
            ".".join(fpath.name.split(".")[2:])
            # fname
            for fpath in (
                s3.get_experiment_subject_directory(experiment, subject) / "offs"
            ).glob(f"{probe}*spatial_offs*")
        ]
    )  # Nasty sh*t good luck lol
    spatial_off_vars = {}
    for suffix in spatial_off_fname_suffixes:
        var_off = tk.BooleanVar()
        checkbox = tk.Checkbutton(
            window, text=f"Display spatial offs: {suffix}", variable=var_off
        )
        checkbox.pack()
        spatial_off_vars[suffix] = var_off
structs_vars = {}
if has_spwrs:
    var_spwrs = tk.BooleanVar()
    checkbox = tk.Checkbutton(
        window, text="Display sharp waves and ripples", variable=var_spwrs
    )
    checkbox.pack()
for acronym in singleprobe_sorting.structures_by_depth:
    N_units = (singleprobe_sorting.properties.acronym == acronym).sum()
    structs_vars[acronym] = tk.BooleanVar()
    checkbox = tk.Checkbutton(
        window,
        text=f"Display structure '{acronym}' (N={N_units})",
        variable=structs_vars[acronym],
    )
    checkbox.pack()
    if N_units > 10:
        checkbox.select()
tk.Button(text="Submit", command=window.destroy).pack()
window.mainloop()


app = ephyviewer.mkQApp()
window = ephyviewer.MainViewer(
    debug=True, show_auto_scale=False, global_xsize_zoom=True
)

if has_hypno and var_hypno.get():
    window = units.ephyviewerutils.add_hypnogram_view_to_window(window, hg)

if has_scorsig and var_scorsig.get():
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
    window = units.ephyviewerutils.add_traceviewer_to_window(
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
    window = units.ephyviewerutils.add_traceviewer_to_window(
        window,
        emg.data,
        1 / tdiff,
        t_start,
        channel_names=emg.signal.data,
        view_name="derived EMG",
        view_params=view_params,
    )


if has_off:
    for suffix, var_off in global_off_vars.items():
        if not var_off.get():
            continue
        offs_df = s3.load_offs_df(
            experiment,
            subject,
            probe,
            off_fname_suffix=suffix,
        )
        if not len(offs_df):
            continue
        window = units.ephyviewerutils.add_epochviewer_to_window(
            window,
            offs_df,
            view_name=f"{suffix}",
            name_column="structure",
            add_event_list=True,
        )

if has_spwrs and var_spwrs.get():
    print("Loading sharp waves and ripples")

    def get_ephyviewer_epochs_dict(df: pd.DataFrame, name: str) -> tuple[dict, dict]:
        durations = (df["end_time"] - df["start_time"]).values
        labels = np.array([f"{name} {i}" for i in df.index.values])
        times = df["start_time"].values

        return {"time": times, "duration": durations, "label": labels, "name": name}

    spw_file = slfp.get_experiment_subject_file(experiment, subject, "spws.pqt")
    spws = pd.read_parquet(spw_file).sort_values("start_time").reset_index(drop=True)
    spw_epochs = get_ephyviewer_epochs_dict(spws, "SPW")

    ripples_file = slfp.get_experiment_subject_file(experiment, subject, "ripples.pqt")
    ripples = (
        pd.read_parquet(ripples_file).sort_values("start_time").reset_index(drop=True)
    )
    ripple_epochs = get_ephyviewer_epochs_dict(ripples, "Ripple")

    epoch_source = ephyviewer.InMemoryEpochSource(
        all_epochs=[spw_epochs, ripple_epochs]
    )
    epoch_view = ephyviewer.EpochViewer(source=epoch_source, name="SPWRs")
    window.add_view(epoch_view, location="bottom", orientation="vertical")

    # event_view = ephyviewer.EventList(source=epoch_source, name="Event List")
    # window.add_view(event_view, orientation="horizontal")

tgt_struct_acronyms = [a for a, v in structs_vars.items() if v.get()]

source_structures = singleprobe_sorting.si_obj.get_annotation("structure_table")
for tgt_struct in tgt_struct_acronyms:
    if has_spatial_off:
        for suffix, var_off in spatial_off_vars.items():
            if not var_off.get():
                continue

            spatial_offs_df = s3.load_offs_df(
                experiment,
                subject,
                probe,
                off_fname_suffix=suffix,
            )
            spatial_offs_df = spatial_offs_df[
                spatial_offs_df["structure"] == tgt_struct
            ]

            if not len(spatial_offs_df):
                continue

            struct_row = source_structures.set_index("acronym").loc[tgt_struct]
            ylim = struct_row["lo"], struct_row["hi"]

            window = units.ephyviewerutils.add_spatialoff_viewer_to_window(
                window,
                spatial_offs_df,
                view_name=f"Spatial off: {tgt_struct}, ylim={ylim}, suffix={suffix}",
                ylim=ylim,
                add_event_list=True,
            )

    window = units.ephyviewerutils.add_spiketrain_views_from_sorting(
        window,
        singleprobe_sorting,
        by="depth",
        tgt_struct_acronyms=[tgt_struct],
        group_by_structure=True,
    )

window.show()
app.exec()

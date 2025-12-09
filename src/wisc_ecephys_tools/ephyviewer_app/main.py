# TODO: Should we remove all usage of 'alias'? Is it ever not "full"?
# TODO: This entire file is an absolute mess.

from . import utils

EXPERIMENT_ALIAS_LIST = [
    ("novel_objects_deprivation", "full"),
    ("sst-experiment", "full"),
    ("auditory_stim", "full"),
    ("discoflow-day1", "full"),
    ("discoflow-day2", "full"),
    ("discoflow-day3", "full"),
]

# Full fname is f"{prb}.{acronym}.{OFF_FNAME_SUFFIX}""
DF_OFF_FNAME_SUFFIX = "global_offs_bystate_conservative_0.05.htsv"


def get_available_sortings(experiment, alias):
    # Import only when needed
    import wisc_ecephys_tools as wet

    # Get the available sortings
    s3 = wet.get_sglx_project("shared")
    sortings_dir = s3.get_alias_directory(experiment, alias)
    return {
        subj.name: [
            x.name.removeprefix("sorting.") for x in sorted(subj.glob("sorting.imec*"))
        ]
        for subj in sortings_dir.iterdir()
        if subj.is_dir()
    }  # e.g. {'CNPIX4-Doppio': ['imec0', 'imec1], 'CNPIX9-Luigi: ['imec0], ...}


def load_offs_df(
    project,  # wne.Project - but we avoid the import at module level
    experiment: str,
    subject: str,
    probe: str,
    off_fname_suffix: str = DF_OFF_FNAME_SUFFIX,
):
    """Load and aggregate off files across structures.

    Loads and aggregate all files of the form
    `<probe>.<acronym>.<off_fname_suffix>` in the `offs` subdirectory
    of the project's experiment_subject_directory.
    """
    import pandas as pd

    from ecephys import utils as ecephys_utils

    off_dir = project.get_experiment_subject_directory(experiment, subject) / "offs"

    structure_offs = []
    for f in off_dir.glob(f"{probe}.*{off_fname_suffix}"):
        structure_offs.append(ecephys_utils.read_htsv(f))

    return pd.concat(structure_offs).reset_index(drop=True)


def run():
    # Import heavy libraries only when needed
    import sys
    import tkinter as tk

    import ephyviewer
    import matplotlib
    import numpy as np
    import pandas as pd
    import rich
    import xarray as xr
    from ephyviewer import CsvEpochSource, EpochEncoder

    import ecephys.plot
    import ecephys.utils.pandas as pd_utils
    import wisc_ecephys_tools as wet
    from ecephys import wne

    # Get the available sortings, per experiment
    s3 = wet.get_sglx_project("shared")
    nb = wet.get_sglx_project("shared_nobak")
    available_sortings = {
        (experiment, alias): get_available_sortings(experiment, alias)
        for experiment, alias in EXPERIMENT_ALIAS_LIST
    }

    # Collect info about the various sortings, for display, and for determing parameters to use when loading
    has_hypnogram = {}
    has_anatomy = {}
    has_off_df = {}
    has_spatial_off_df = {}
    has_scoring_sigs = {}
    has_sharp_wave_ripples = {}
    has_mu_spindles = {}
    has_stimulus_times = {}
    for experiment, alias in EXPERIMENT_ALIAS_LIST:
        has_hypnogram[(experiment, alias)] = {
            subject: s3.get_experiment_subject_file(
                experiment, subject, "hypnogram.htsv"
            ).exists()
            for subject in available_sortings[(experiment, alias)]
        }  # TODO: This should just be checked in the load_multiprobe_sorting function.... TB: Yes but it would require (slowish) loading of all sortings
        has_anatomy[(experiment, alias)] = {
            subject: {
                probe: s3.get_experiment_subject_file(
                    experiment, subject, f"{probe}.structures.htsv"
                ).exists()
                for probe in probes
            }
            for subject, probes in available_sortings[(experiment, alias)].items()
        }  # TODO: This should just be checked in the load_multiprobe_sorting function.... TB: Yes but it would require (slowish) loading of all sortings
        off_fname_glob = "*global_offs_*"
        has_off_df[(experiment, alias)] = {
            subject: {
                probe: len(
                    list(
                        (
                            s3.get_experiment_subject_directory(experiment, subject)
                            / "offs"
                        ).glob(f"{probe}{off_fname_glob}")
                    )
                )
                > 0
                for probe in probes
            }
            for subject, probes in available_sortings[(experiment, alias)].items()
        }  # TODO: This should just be checked in the load_multiprobe_sorting function.... TB: Yes but it would require (slowish) loading of all sortings
        spatial_off_fname_glob = "*spatial_offs_*"
        has_spatial_off_df[(experiment, alias)] = {
            subject: {
                probe: len(
                    list(
                        (
                            s3.get_experiment_subject_directory(experiment, subject)
                            / "offs"
                        ).glob(f"{probe}{spatial_off_fname_glob}")
                    )
                )
                > 0
                for probe in probes
            }
            for subject, probes in available_sortings[(experiment, alias)].items()
        }  # TODO: This should just be checked in the load_multiprobe_sorting function.... TB: Yes but it would require (slowish) loading of all sortings
        has_scoring_sigs[(experiment, alias)] = {
            subject: all(
                [
                    nb.get_experiment_subject_file(experiment, subject, fname).exists()
                    for fname in ["scoring_lfp.zarr", "scoring_emg.zarr"]
                ]
            )
            for subject in available_sortings[(experiment, alias)]
        }  # TODO: This should just be checked in the load_multiprobe_sorting function.... TB: Yes but it would require (slowish) loading of all sortings
        has_sharp_wave_ripples[(experiment, alias)] = {
            subject: (
                nb.get_experiment_subject_file(
                    experiment, subject, "postprocessed_spws.pqt"
                ).exists()
                and nb.get_experiment_subject_file(
                    experiment, subject, "postprocessed_ripples.pqt"
                ).exists()
            )
            for subject in available_sortings[(experiment, alias)]
        }
        has_mu_spindles[(experiment, alias)] = {
            subject: {
                probe: len(
                    list(
                        nb.get_experiment_subject_directory(experiment, subject).glob(
                            f"{probe}*mu_spindles*"
                        )
                    )
                )
                > 0
                for probe in probes
            }
            for subject, probes in available_sortings[(experiment, alias)].items()
        }
        has_stimulus_times[(experiment, alias)] = {
            subject: (
                s3.get_experiment_subject_file(
                    experiment, subject, "stimulus_times.htsv"
                ).exists()
            )
            for subject in available_sortings[(experiment, alias)]
        }

    sortings_summary = {
        (experiment, alias): {
            subject: {
                "probes": available_sortings[(experiment, alias)][subject],
                "anatomy": has_anatomy[(experiment, alias)][subject],
                "hypnogram": has_hypnogram[(experiment, alias)][subject],
                "scoring_sigs": has_scoring_sigs[(experiment, alias)][subject],
                "global offs": has_off_df[(experiment, alias)][subject],
                "spatial offs": has_spatial_off_df[(experiment, alias)][subject],
                "spwrs": has_sharp_wave_ripples[(experiment, alias)][subject],
                "mu_spindles": has_mu_spindles[(experiment, alias)][subject],
                "stimulus times": has_stimulus_times[(experiment, alias)][subject],
            }
            for subject in available_sortings[experiment, alias]
        }
        for experiment, alias in EXPERIMENT_ALIAS_LIST
    }

    # Simple GUI dialog for getting the desired probe
    root = tk.Tk()
    tk.Label(root, text="Available sortings").pack()
    txt = tk.Text(root)
    txt.insert(tk.END, rich.pretty.pretty_repr(sortings_summary))
    txt.pack(anchor="w")
    # Position radio buttons within scrollable frame (too many sortings !): https://stackoverflow.com/a/71682458
    outer_frame = tk.Frame(root)  # Contains canvas and scrollbar
    outer_frame.pack(fill=tk.BOTH, expand=1)
    # canvas
    my_canvas = tk.Canvas(outer_frame)
    my_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
    # scrollbar
    my_scrollbar = tk.Scrollbar(
        outer_frame, orient=tk.VERTICAL, command=my_canvas.yview
    )
    my_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    # Frame within canvas, containing buttons
    second_frame = tk.Frame(my_canvas, width=1000, height=100)
    # configure the scrollable canvas
    my_canvas.configure(yscrollcommand=my_scrollbar.set)
    my_canvas.bind(
        "<Configure>", lambda e: my_canvas.configure(scrollregion=my_canvas.bbox("all"))
    )
    my_canvas.configure(scrollregion=my_canvas.bbox("all"))
    v = tk.IntVar()
    available_subject_probes = [(None, None, None, None)]
    for experiment, alias in available_sortings:
        for subj, prbs in available_sortings[(experiment, alias)].items():
            available_subject_probes += [(experiment, alias, subj, prb) for prb in prbs]
    for i, (experiment, alias, subj, prb) in enumerate(available_subject_probes):
        tk.Radiobutton(
            second_frame,
            text=f"{experiment}, {alias} : {subj}, {prb}",
            variable=v,
            value=i,
        ).pack(anchor="w")
    tk.Button(text="Submit", command=root.destroy).pack()
    my_canvas.create_window((0, 0), window=second_frame, anchor="nw")

    root.mainloop()
    subj_prb_i = v.get()
    if subj_prb_i == 0:  # If window was closed without making a selection
        sys.exit()
    experiment, alias, subject, probe = available_subject_probes[subj_prb_i]
    print(f"\nLoading: {experiment}, {alias}, {subject}, {probe}\n")

    # Load the sorting
    sglx_subject = wet.get_sglx_subject(subject)
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

    if has_hypnogram[(experiment, alias)][subject]:
        params = s3.load_experiment_subject_params(experiment, sglx_subject)
        hg = wet.rats.exp_hgs.load_hypnogram(
            s3,
            experiment,
            sglx_subject,
            probes=params["hypnogram_probe"],  # Possibly should just be `probe`
            include_ephyviewer_edits=True,
            include_sorting_nodata=False,
            include_lf_consolidated_artifacts=False,
            include_ap_consolidated_artifacts=False,
            include_lf_sglx_filetable_nodata=False,
            include_ap_sglx_filetable_nodata=False,
            simplify=True,
        )  # This may fail, because it used to look for a probe-agnostic hypnogram at
        # `s3.get_experiment_subject_file(experiment, sglx_subject, "hypnogram.htsv")`.
    singleprobe_sorting = wne.sglx.legacy_sorting.load_singleprobe_sorting(
        s3,
        sglx_subject,
        experiment,
        probe,
        alias=alias,
        sorting=sorting,
        postprocessing=postprocessing,
        allow_no_sync_file=True,
    )
    singleprobe_sorting = singleprobe_sorting.refine_clusters(
        filters,
        include_nans=True,
    )

    has_off = has_off_df[(experiment, alias)][subject][probe]
    has_spatial_off = has_spatial_off_df[(experiment, alias)][subject][probe]
    has_hypno = has_hypnogram[(experiment, alias)][subject]
    has_scorsig = has_scoring_sigs[(experiment, alias)][subject]
    has_spwrs = has_sharp_wave_ripples[(experiment, alias)][subject]
    has_mu_spindles = has_mu_spindles[(experiment, alias)][subject][probe]
    has_stims = has_stimulus_times[(experiment, alias)][subject]

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
    var_hypno_encoder = tk.BooleanVar()
    checkbox = tk.Checkbutton(
        window, text="Allow hypnogram edits", variable=var_hypno_encoder
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
            if suffix == DF_OFF_FNAME_SUFFIX:
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
    if has_mu_spindles:
        var_muspins = tk.BooleanVar()
        checkbox = tk.Checkbutton(
            window,
            text="Display multi-unit-based spindle detection",
            variable=var_muspins,
        )
        checkbox.pack()
    if has_stims:
        var_stims = tk.BooleanVar()
        checkbox = tk.Checkbutton(
            window, text="Display stimulus times", variable=var_stims
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
    var_pool = tk.BooleanVar()
    checkbox = tk.Checkbutton(
        window, text="Pool selected structures in the same panel", variable=var_pool
    )
    checkbox.pack()
    tk.Button(text="Submit", command=window.destroy).pack()
    window.mainloop()

    app = ephyviewer.mkQApp()
    window = ephyviewer.MainViewer(
        debug=True, show_auto_scale=False, global_xsize_zoom=True
    )

    if has_hypno and var_hypno.get():
        window = utils.add_hypnogram_view_to_window(window, hg)

    if has_scorsig and var_scorsig.get():
        print("Loading scoring signals")
        lfp = xr.open_dataarray(
            nb.get_experiment_subject_file(experiment, subject, "scoring_lfp.zarr"),
            engine="zarr",
        )
        emg = xr.open_dataarray(
            nb.get_experiment_subject_file(experiment, subject, "scoring_emg.zarr"),
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
        window = utils.add_traceviewer_to_window(
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
        window = utils.add_traceviewer_to_window(
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
            window = utils.add_epochviewer_to_window(
                window,
                offs_df,
                view_name=f"{suffix}",
                name_column="structure",
                add_event_list=True,
            )

    if has_spwrs and var_spwrs.get():
        print("Loading sharp waves and ripples")

        def get_ephyviewer_epochs_dict(
            df: pd.DataFrame, name: str
        ) -> tuple[dict, dict]:
            durations = (df["end_time"] - df["start_time"]).values
            labels = np.array([f"{name} {i}" for i in df.index.values])
            times = df["start_time"].values

            return {"time": times, "duration": durations, "label": labels, "name": name}

        spw_file = nb.get_experiment_subject_file(
            experiment, subject, "postprocessed_spws.pqt"
        )
        spws = (
            pd.read_parquet(spw_file).sort_values("start_time").reset_index(drop=True)
        )
        spw_epochs = get_ephyviewer_epochs_dict(spws, "SPW")

        ripples_file = nb.get_experiment_subject_file(
            experiment, subject, "postprocessed_ripples.pqt"
        )
        ripples = (
            pd.read_parquet(ripples_file)
            .sort_values("start_time")
            .reset_index(drop=True)
        )
        ripple_epochs = get_ephyviewer_epochs_dict(ripples, "Ripple")

        epoch_source = ephyviewer.InMemoryEpochSource(
            all_epochs=[spw_epochs, ripple_epochs]
        )
        epoch_view = ephyviewer.EpochViewer(source=epoch_source, name="SPWRs")
        window.add_view(epoch_view, location="bottom", orientation="vertical")

        # event_view = ephyviewer.EventList(source=epoch_source, name="Event List")
        # window.add_view(event_view, orientation="horizontal")

    if has_mu_spindles and var_muspins.get():
        print("Loading MU-spindles")

        muspin_files = nb.get_experiment_subject_directory(experiment, subject).glob(
            f"{probe}.*.mu_spindles.pqt"
        )
        muspindles = (
            pd.concat([pd.read_parquet(muspin_file) for muspin_file in muspin_files])
            .sort_values(by="Start")
            .reset_index(drop=True)
        )
        muspindles["start_time"] = muspindles["Start"]
        muspindles["duration"] = muspindles["End"] - muspindles["Start"]

        window = utils.add_epochviewer_to_window(
            window,
            muspindles,
            view_name="MU-based spindles",
            name_column="Structure",
            add_event_list=True,
        )

    if has_stims and var_stims.get():
        print("Loading stimulus times")

        stims_file = s3.get_experiment_subject_file(
            experiment, subject, "stimulus_times.htsv"
        )
        stims = pd_utils.read_htsv(stims_file)

        def get_ephyviewer_epochs_dict(
            df: pd.DataFrame, name: str
        ) -> tuple[dict, dict]:
            durations = (df["offset"] - df["onset"]).values
            labels = np.array([f"{name} {i}" for i in df.index.values])
            times = df["onset"].values

            return {"time": times, "duration": durations, "label": labels, "name": name}

        stim_epochs = get_ephyviewer_epochs_dict(stims, "Stim")

        epoch_source = ephyviewer.InMemoryEpochSource(all_epochs=[stim_epochs])
        epoch_view = ephyviewer.EpochViewer(source=epoch_source, name="Stims")
        window.add_view(epoch_view, location="bottom", orientation="vertical")

        # Add event list for navigation
        view = ephyviewer.EventList(source=epoch_source, name="Stims list")
        window.add_view(view, orientation="horizontal", split_with="Stims")

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

                window = utils.add_spatialoff_viewer_to_window(
                    window,
                    spatial_offs_df,
                    view_name=f"Spatial off: {tgt_struct}, ylim={ylim}, suffix={suffix}",
                    ylim=ylim,
                    add_event_list=True,
                )

        if not var_pool.get():
            # Separate view for each structure
            # Below each spatial off
            window = utils.add_spiketrain_views_from_sorting(
                window,
                singleprobe_sorting,
                by="depth",
                tgt_struct_acronyms=[tgt_struct],
                group_by_structure=True,
            )

    if var_pool.get() and len(tgt_struct_acronyms):
        # Same view for all structures,
        # below all offs
        window = utils.add_spiketrain_views_from_sorting(
            window,
            singleprobe_sorting,
            by="depth",
            tgt_struct_acronyms=tgt_struct_acronyms,
            group_by_structure=False,
        )

    if var_hypno_encoder.get():
        print("Add hypnogram edits encoder")
        edits_fpath = s3.get_experiment_subject_file(
            experiment, subject, wet.constants.Files.HYPNOGRAM_EPHYVIEWER_EDITS
        )

        states = utils.EPHYVIEWER_STATE_ORDER
        source_epoch = CsvEpochSource(
            edits_fpath,
            states,
            color_labels=[
                matplotlib.colors.rgb2hex(ecephys.plot.state_colors[state])
                for state in states
            ],
        )
        encoder_view = EpochEncoder(source=source_epoch, name="Hypnogram edits")
        encoder_view.params["label_fill_color"] = "#00000000"  # Full transparent
        window.add_view(encoder_view)

    window.show()
    app.exec()

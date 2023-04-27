import pathlib
import sys
import tkinter as tk

import rich

from ecephys import wne
from ecephys.wne.utils import load_multiprobe_sorting
import wisc_ecephys_tools as wet

experiment = "novel_objects_deprivation"
alias = "full"


# Get the available sortings
ss = wne.ProjectLibrary(wet.get_projects_file()).get_project("shared_sortings")
s3 = wne.ProjectLibrary(wet.get_projects_file()).get_project("shared_s3")
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
}  # TODO: This should just be checked in the load_multiprobe_sorting function....
has_anatomy = {
    subject: {
        probe: s3.get_experiment_subject_file(
            experiment, subject, f"{probe}.structures.htsv"
        ).exists()
        for probe in probes
    }
    for subject, probes in available_sortings.items()
}  # TODO: This should just be checked in the load_multiprobe_sorting function....
sortings_summary = {
    subject: {
        "probes": available_sortings[subject],
        "anatomy": has_anatomy[subject],
        "hypnogram": has_hypnogram[subject],
    }
    for subject in available_sortings
}

# Simple GUI dialog for getting the desired subject
root = tk.Tk()
tk.Label(root, text="Available sortings").pack()
txt = tk.Text(root)
txt.insert(tk.END, rich.pretty.pretty_repr(sortings_summary))
txt.pack(anchor="w")
v = tk.IntVar()
available_subjects = list(available_sortings)
for i, subj in enumerate(available_subjects):
    tk.Radiobutton(root, text=subj, variable=v, value=i).pack(anchor="w")
tk.Button(text="Submit", command=root.destroy).pack()
root.mainloop()
selection = v.get()
if selection == 0:  # If window was closed without making a selection
    sys.exit()
subject = available_subjects[selection]

# Load the sorting
wneSubject = wne.sglx.SubjectLibrary(wet.get_subjects_directory()).get_subject(subject)
probes = available_sortings[subject]
sortings = {prb: "sorting" for prb in probes}
postprocessings = {prb: "postpro" for prb in probes}
default_filters = {
    "quality": {
        "good",
        "mua",
    },  # "quality" property is "group" from phy curation. Remove noise
    "firing_rate": (0.5, float("Inf")),
    # ...
}
filters = {prb: default_filters for prb in probes}

wneHypnogramProject = s3 if has_hypnogram[subject] else None
wneAnatomyProject = s3 if all(has_anatomy[subject].values()) else None
multiprobe_sorting = load_multiprobe_sorting(
    ss,
    wneSubject,
    experiment,
    alias,
    probes,
    sortings=sortings,
    postprocessings=postprocessings,
    wneAnatomyProject=wneAnatomyProject,
    wneHypnogramProject=wneHypnogramProject,
)
multiprobe_sorting = multiprobe_sorting.refine_clusters(filters)
multiprobe_sorting.plot_interactive_ephyviewer_raster(by="depth")

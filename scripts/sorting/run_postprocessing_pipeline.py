#!/usr/bin/env python
# coding: utf-8

"""Run postprocessing pipeline.

Modify script to change default argument values

Usage:
  run_postprocessing_pipeline.py [options] [--input <subjectName>,<probeName>,<sorting_basename>]...

Options:
  -h --help                          Show this screen.
  --input==<subjectName,probeName>   (Repeatable) Comma-separated pair of the form `<subjectName>,<probeName>`. We assume the sorting directory's basename is `sorting`
  --from_folder                      (re)run from existing folder. Should not specify exclusions or opts if so.
  --projectName==<pn>                Project name. Output path pulled from wisc_ecephys_tools's projects.yaml file
  --experimentName==<en>             Experiment
  --aliasName==<an>                  Alias name
  --hypnogramProject==<pn>           Project we pull the hypnograms from. Required if the options specify per-vigilance-state postprocessing
  --optionsPath==<opts>              Path to options file (applied to all input datasets)
  --n_jobs=<n_jobs>                  Number of jobs for all spikeinterface functions. [default: 10]
"""

from pathlib import Path

from docopt import docopt
from lnsp.postprocessing_pipeline import (
    SpikeInterfacePostprocessingPipeline,
)

import wisc_ecephys_tools as wet

BASENAME_DF = "sorting"
RERUN_EXISTING_DF = False

if __name__ == "__main__":
    args = docopt(__doc__, version="Naval Fate 2.0")

    print(args)

    print(f"Running all subject/probe pairs: {args['--input']}")

    for subject_probe in args["--input"]:
        subjectName, probe = subject_probe.split(",")

        sglxSubject = wet.get_sglx_subject(subjectName)
        sglx_project = wet.get_sglx_project(args["--projectName"])

        # Output dirname from options filename
        postprocessing_name = (
            Path(args["--optionsPath"]).name.replace(".yaml", "").replace(".yml", "")
        )

        # Pull hypno
        if args["--hypnogramProject"]:
            hypnogram_source = wet.get_wne_project(args["--hypnogramProject"])
        else:
            hypnogram_source = None
        print(hypnogram_source)

        postpro_pipeline = SpikeInterfacePostprocessingPipeline(
            sglx_project,
            sglxSubject,
            args["--experimentName"],
            args["--aliasName"],
            probe,
            sorting_basename=BASENAME_DF,
            postprocessing_name=postprocessing_name,
            rerun_existing=RERUN_EXISTING_DF,
            n_jobs=args["--n_jobs"],
            options_source=args["--optionsPath"],
            hypnogram_source=hypnogram_source,
        )
        print(f"Postpro pipeline: {postpro_pipeline}\n")
        print(f"Pipeline opts: {postpro_pipeline._opts}")

        postpro_pipeline.run_postprocessing()

        print("\n\n ...Done!")

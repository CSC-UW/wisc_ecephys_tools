#!/usr/bin/env python
# coding: utf-8

"""Run sorting pipeline.

Usage:
  run_sorting_pipeline.py [options] [--input <subjectName>,<probeName>]...
  run_sorting_pipeline.py [options] (--prepro_only) [--input <subjectName>,<probeName>]...

Options:
  -h --help                          Show this screen.
  --input==<subjectName,probeName>   (Repeatable) Comma-separated pair of the form `<subjectName>,<probeName>`
  --from_folder                      (Re)run, loading opts.yml and segments.htsv from existing folder. Should not specify exclusions or opts if so.
  --prepro_only                      Run only preprocessing, not full pipeline (drift correction)
  --projectName==<pn>                Project name. Output path pulled from wisc_ecephys_tools's projects.yaml file
  --experimentName==<en>             Experiment
  --aliasName==<an>                  Alias name
  --optionsPath==<opts>              Path to options file (applied to all input datasets)
  --n_jobs=<n_jobs>                  Number of jobs for all spikeinterface functions. [default: 10]

"""

from docopt import docopt
from lnsp.sorting_pipeline import SpikeInterfaceSortingPipeline

import wisc_ecephys_tools as wet

BASENAME_DF = "sorting"
RERUN_EXISTING_DF = False
EXCLUSIONS_PROJECT = "shared"

if __name__ == "__main__":
    args = docopt(__doc__, version="Naval Fate 2.0")

    print(f"Running all subject/probe pairs: {args['--input']}")

    for subject_probe in args["--input"]:
        subjectName, probe = subject_probe.split(",")

        sglxSubject = wet.get_sglx_subject(subjectName)
        sglxProject = wet.get_sglx_project(args["--projectName"])
        exclusionsProject = wet.get_wne_project(EXCLUSIONS_PROJECT)

        if not args["--from_folder"]:
            sorting_pipeline = SpikeInterfaceSortingPipeline(
                sglxProject,
                sglxSubject,
                args["--experimentName"],
                args["--aliasName"],
                probe,
                basename=BASENAME_DF,
                rerun_existing=RERUN_EXISTING_DF,
                n_jobs=int(args["--n_jobs"]),
                options_source=args["--optionsPath"],
                exclusions_source=exclusionsProject,
            )

        else:
            assert not args["--optionsPath"], (
                "Should not specify '--optionsPath' argument if using '--from_folder' option."
            )
            sorting_pipeline = SpikeInterfaceSortingPipeline.load_from_folder(
                sglxProject,
                sglxSubject,
                args["--experimentName"],
                args["--aliasName"],
                probe,
                basename=BASENAME_DF,
                rerun_existing=RERUN_EXISTING_DF,
                n_jobs=int(args["--n_jobs"]),
            )

        # Load raw recording and semgments
        sorting_pipeline.get_raw_si_recording()
        print(f"Sorting pipeline: {sorting_pipeline}\n")
        print(f"Pipeline opts: {sorting_pipeline.opts}")
        print(f"Raw recording:\n {sorting_pipeline._raw_si_recording}")

        if args["--prepro_only"]:
            print("--prepro_only==True: Run only preprocessing")
            sorting_pipeline.run_preprocessing()
        else:
            print("Run full pipeline")
            sorting_pipeline.run_preprocessing()
            sorting_pipeline.run_sorting()

        print(f"Sorting pipeline: {sorting_pipeline}\n")
        print(f"Pipeline opts: {sorting_pipeline._opts}\n")
        print(f"Raw recording:\n {sorting_pipeline._raw_si_recording}\n")

        print("\n\n ...Done!")

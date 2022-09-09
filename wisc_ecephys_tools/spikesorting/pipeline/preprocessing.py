# This basically runs CatGT -- there is no additional preprocessing.

from datetime import datetime

import ecephys.data_mgmt.paths
from ecephys.sglx.cat_gt import run_catgt
from ecephys.sglx.file_mgmt import loc
from ecephys.sglx.utils import get_meta_value
from ..params import get_analysis_params
from ...projects.projects import get_alias_subject_directory
from ...sglx.experiments import get_ap_bin_table
from ...sglx.sessions import get_session_style_path_parts

CATGT_PROJECT_NAME = "catgt"  # Key in projects.yaml.
ANALYSIS_TYPE = "preprocessing"  # Relevant analysis type in analysis_cfg.yaml


def get_analysis_dir(
    project=None,
    subject=None,
    experiment=None,
    alias=None,
    analysis_name=None,
    subalias_idx=None,
):
    """
    Catgt target directory. Output data is at analysis_dir/catgt_gate_dir/catgt_probe_dir

    project/
        experiment/
            alias_dir/
                subject/
                    analysis_name/
    """
    return (
        get_alias_subject_directory(
            project, experiment, alias, subject, subalias_idx=subalias_idx
        )
        / analysis_name
    )


def get_catgt_output_paths(
    project=CATGT_PROJECT_NAME,
    subject=None,
    experiment=None,
    alias=None,
    probe=None,
    analysis_name=None,
):
    """Return list of catgt output paths for each subalias: [(metapath_0, binpath_0), ..]

    CatGT data is saved following standard SGLX folder-per-probe structure in the analysis dir
    for each subalias: analysis_dir/catgt_gate_dir/catgt_probe_dir
    """
    assert all([arg is not None for arg in [subject, experiment, alias, probe]])

    raw_files = get_ap_bin_table(
        subject,
        experiment,
        alias,
        probe=probe,
    )
    subalias_indices = sorted(raw_files.subalias_idx.unique())

    meta_bin_paths = []
    for subalias_idx in subalias_indices:

        analysis_dir = get_analysis_dir(
            project=project,
            experiment=experiment,
            alias=alias,
            subject=subject,
            analysis_name=analysis_name,
            subalias_idx=subalias_idx,
        )
        subalias_files = loc(raw_files, subalias_idx=subalias_idx).reset_index()

        # This is necessary because catgt changes gate and probe dirnames
        fname = subalias_files.path.values[0].name
        ext = ".ap.bin"
        stem = fname.split(ext)[0]
        run, gate, trigger, probe = ecephys.data_mgmt.paths.parse_sglx_stem(stem)
        # In catGT2.4 it's always g0 (Bill's mistake I think)
        # catgt_gate = 'g0'
        catgt_gate_dirname = f"catgt_{run}_{gate}"
        catgt_probe_dirname = f"{run}_{gate}_{probe}"

        parent_dir = analysis_dir / catgt_gate_dirname / catgt_probe_dirname
        metastem = f"{run}_{gate}_tcat.{probe}.ap.meta"
        binstem = f"{run}_{gate}_tcat.{probe}.ap.bin"

        meta_bin_paths.append((parent_dir / metastem, parent_dir / binstem))

    return meta_bin_paths


def clear_catgt_output_files(*args, **kwargs):
    meta_bin_paths = get_catgt_output_paths(*args, **kwargs)
    if any([m.exists() or b.exists() for m, b in meta_bin_paths]):
        print("Removing bin and meta catGT output files.")
    else:
        print("Found no bin and meta catGT output files to remove.")
    for metapath, binpath in meta_bin_paths:
        if metapath.exists():
            print(f"Remove {metapath}")
            metapath.unlink()
        if binpath.exists():
            print(f"Remove {binpath}")
            binpath.unlink()


def check_all_exists_catgt_output(*args, **kwargs):
    metapaths, binpaths = zip(*get_catgt_output_paths(*args, **kwargs))
    return all([f.exists() for f in metapaths + binpaths])


def check_any_exists_catgt_output(*args, **kwargs):
    metapaths, binpaths = zip(*get_catgt_output_paths(*args, **kwargs))
    return any([f.exists() for f in metapaths + binpaths])


def run_preprocessing(
    project=CATGT_PROJECT_NAME,
    subject=None,
    experiment=None,
    alias=None,
    probe=None,
    analysis_name=None,
    rerun_existing=False,
    dry_run=True,
):
    """Run CatGT for each subalias. Return 1 if the command finished running."""
    assert all(
        [
            arg is not None
            for arg in [project, subject, experiment, alias, probe, analysis_name]
        ]
    )

    # rerun_existing logic
    any_output = check_any_exists_catgt_output(
        project=project,
        subject=subject,
        experiment=experiment,
        alias=alias,
        probe=probe,
        analysis_name=analysis_name,
    )
    all_output = check_any_exists_catgt_output(
        project=project,
        subject=subject,
        experiment=experiment,
        alias=alias,
        probe=probe,
        analysis_name=analysis_name,
    )
    if not rerun_existing:
        if any_output and not all_output:
            raise Exception(
                f"Aborting catGT run: set `rerun_existing` == True or delete (partial) preexisting files."
            )
        if all_output:
            print(f"`rerun_existing` == True and all files were found.\nDoing nothing.")
            return True
    elif rerun_existing and not dry_run:
        print("rerun_existing = True: Deleting preexisting catgt files.")
        clear_catgt_output_files(
            project=project,
            subject=subject,
            experiment=experiment,
            alias=alias,
            probe=probe,
            analysis_name=analysis_name,
        )

    # Gather files and params
    analysis_params = get_analysis_params("preprocessing", analysis_name)
    catgt_params = analysis_params["catgt_params"]
    catgt_path = analysis_params["catgt_path"]
    raw_files = get_ap_bin_table(
        subject,
        experiment,
        alias,
        probe=probe,
        assert_contiguous=True,
    )

    print("\nBelow are all the files that will be processed (all subaliases):")
    print(
        raw_files[
            ["run", "gate", "trigger", "fileTimeSecs", "subalias_idx", "fileCreateTime"]
        ]
    )

    # Run each subalias separately
    subalias_indices = sorted(raw_files.subalias_idx.unique())
    for i, subalias_idx in enumerate(subalias_indices):

        # Subalias files and output dir
        analysis_dir = get_analysis_dir(
            project=project,
            experiment=experiment,
            alias=alias,
            subject=subject,
            subalias_idx=subalias_idx,
            analysis_name=analysis_name,
        )
        subalias_files = loc(raw_files, subalias_idx=subalias_idx).reset_index()

        print(
            f"\nRun subalias #{i + 1}/{len(subalias_indices)}, "
            f"concatenate N={len(subalias_files)} files. "
            f"Total output recording duration should be {subalias_files.fileTimeSecs.astype(float).sum() / 3600}h (in the absence of CatGT-filled gaps)\n"
        )

        # Check that subalias files are all from the same run
        if not len(subalias_files.run.unique()) == 1:
            raise ValueError(
                "Files from a single subalias should all originate from the same run."
                f"Please specify N={len(subalias_files.run.unique())} different subaliases"
                f"for the following files: "
                f"{subalias_files[['run', 'gate', 'trigger', 'fileTimeSecs', 'subalias_idx', 'fileCreateTime']]}"
            )

        # Src and target dirs
        (
            root_dir,
            subject_dirname,
            session_dirname,
            session_sglx_dirname,
            _,
            _,
            _,
        ) = get_session_style_path_parts(subalias_files.path[0])
        src_dir = root_dir / subject_dirname / session_dirname / session_sglx_dirname
        tgt_dir = analysis_dir

        start = datetime.now()
        run_catgt(
            subalias_files, catgt_params, catgt_path, src_dir, tgt_dir, dry_run=dry_run
        )
        end = datetime.now()

        print(
            f"{end.strftime('%H:%M:%S')}: Finished {subject}, {experiment}, {alias}, subalias #{i+1}/{len(subalias_indices)}. "
            f"Run time = {str(end - start)}, ",
            end="",
        )
        if not dry_run:
            # Extract the output file duration (sanity check)
            output_binpath, _ = get_catgt_output_paths(
                project=project,
                subject=subject,
                experiment=experiment,
                alias=alias,
                probe=probe,
                analysis_name=analysis_name,
            )[i]
            output_duration = get_meta_value(output_binpath, "fileTimeSecs")
            print(f"Output file duration = {float(output_duration) / 3600}sec")

    # The command finished if we find the meta file (since it's written at the end)
    subaliases_metapaths, subaliases_binpaths = zip(
        *get_catgt_output_paths(
            project=project,
            subject=subject,
            experiment=experiment,
            alias=alias,
            probe=probe,
            analysis_name=analysis_name,
        )
    )
    return all([metapath.exists() for metapath in subaliases_metapaths])

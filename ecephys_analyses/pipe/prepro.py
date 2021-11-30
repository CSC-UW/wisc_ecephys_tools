import ecephys.data_mgmt.paths
from datetime import datetime
import ecephys_analyses.paths
from ecephys_analyses.params import get_analysis_params
from pathlib import Path

from ecephys.sglx.cat_gt import run_catgt


CATGT_PROJECT_NAME = 'catgt'  # Key in projects.yaml.
ANALYSIS_TYPE = 'preprocessing'  # Relevant analysis type in analysis_cfg.yaml


def get_catgt_output_paths(
    subject=None,
    experiment=None,
    alias=None,
    probe=None,
    project=CATGT_PROJECT_NAME,
):
    """Return catgt output paths: (metapath, binpath)."""
    assert all(
        [arg is not None
        for arg in [subject, experiment, alias, probe]]
    )

    analysis_dir = ecephys_analyses.projects.get_project_directory(project)

    # TODO: Check that this is a continuous data and not a "combined" alias
    raw_files = ecephys_analyses.get_ap_bin_files(
        subject,
        experiment,
        alias,
        probe=probe,
    )

    (
        _,
        subject_dirname,
        session_dirname,
        session_sglx_dirname,
        _,
        _,
        fname,
    ) = ecephys_analyses.get_session_style_path_parts(
        raw_files.path.values[0]
    )

    ext = '.ap.bin'
    stem = fname.split(ext)[0]
    run, gate, trigger, probe = ecephys.data_mgmt.paths.parse_sglx_stem(stem)

    # In catGT2.4 it's always g0 (Bill's mistake I think)
    catgt_gate = 'g0'
    catgt_gate_dirname = f'catgt_{run}_{catgt_gate}'
    catgt_probe_dirname = f'{run}_{catgt_gate}_{probe}'

    parent_dir = (
        analysis_dir/
        subject_dirname/
        session_dirname/
        session_sglx_dirname/
        catgt_gate_dirname/
        catgt_probe_dirname
    )

    metastem = f'{run}_{catgt_gate}_tcat.{probe}.ap.meta'
    binstem = f'{run}_{catgt_gate}_tcat.{probe}.ap.bin'

    return parent_dir/metastem, parent_dir/binstem


def clear_catgt_output_files(
    subject=None,
    experiment=None,
    alias=None,
    probe=None,
    project=CATGT_PROJECT_NAME,
):
    print("Removing bin and meta catGT output files.")
    output_metapath, output_binpath = get_catgt_output_paths(
        subject=subject,
        experiment=experiment,
        alias=alias,
        probe=probe,
        project=project
    )
    assert output_binpath.exists()
    output_binpath.unlink()
    assert output_metapath.exists()
    output_metapath.unlink()


def run_preprocessing(
    subject=None,
    experiment=None,
    alias=None,
    probe=None,
    analysis_name=None,
    project=CATGT_PROJECT_NAME,
    rerun_existing=False,
    dry_run=True
):
    """Run CatGT. Return 1 if the command finished running."""
    assert all(
        [arg is not None
        for arg in [subject, experiment, alias, probe, analysis_name]]
    )

    analysis_params = get_analysis_params('preprocessing', analysis_name)

    # Check for existing files
    output_metapath, output_binpath = get_catgt_output_paths(
        subject=subject,
        experiment=experiment,
        alias=alias,
        probe=probe,
        analysis_name=analysis_name,
    )
    if not rerun_existing and (output_binpath.exists() or output_metapath.exists()):
        raise Exception(
            f"Aborting catGT run: set `rerun_existing` == True or delete preexisting files at \n{output_binpath}, \n{output_metapath}."
        )
    elif rerun_existing:
        output_binpath.unlink(missing_ok=True)
        output_metapath.unlink(missing_ok=True)
        
    catgt_params = analysis_params['catgt_params']
    catgt_path = analysis_params['catgt_path']
    analysis_dir = ecephys_analyses.projects.get_project_directory(project)

    raw_files = ecephys_analyses.paths.get_ap_bin_files(
        subject,
        experiment,
        alias,
        probe=probe,
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
    ) = ecephys_analyses.get_session_style_path_parts(
        raw_files.path[0]
    )
    src_dir = root_dir/subject_dirname/session_dirname/session_sglx_dirname
    tgt_dir = analysis_dir/subject_dirname/session_dirname/session_sglx_dirname

    start = datetime.now()
    run_catgt(
        raw_files,
        catgt_params,
        catgt_path,
        src_dir,
        tgt_dir,
        dry_run=dry_run
    )
    end = datetime.now()
    print(f"{end.strftime('%H:%M:%S')}: Finished {subject}, {experiment}, {alias}. Run time = {str(end - start)}")

    # The command finished if we find the meta file (since it's written at the end)
    success = output_binpath.exists() & output_metapath.exists()
    return success
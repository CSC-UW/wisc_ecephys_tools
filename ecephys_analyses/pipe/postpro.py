from pathlib import Path
from datetime import datetime
import subprocess

from ecephys_analyses.params import get_analysis_params
from ecephys_analyses.pipe import get_sorting_output_path
from ecephys_analyses.paths import get_ap_bin_paths

from ecephys_spike_sorting.scripts.create_input_json import createInputJson


def run_postprocessing(
    project=None,
    subject=None,
    experiment=None,
    alias=None,
    probe=None,
    analysis_name=None,
    sorting_analysis_name=None,
    rerun_existing=False,
    dry_run=True
):
    assert all(
        [arg is not None
        for arg in [project, subject, experiment, alias, probe, analysis_name, sorting_analysis_name]]
    )
    print(f"Postprocessing: {locals()}\n")

    # Modules and associated parameters
    modules = []
    params = []
    module_name_params = get_analysis_params(
        'ks_postprocessing',
       analysis_name 
    )
    for d in module_name_params:
        modules += d.keys()
        params += d.values()
    
    # Raw data paths (Sorting was performed on preproed data, but this is only used for sRate channel positions etc)
    raw_paths = get_ap_bin_paths(
        subject,
        experiment,
        alias,
        probe=probe,
    )
    binpath = raw_paths[0]
    metapath = binpath.parent/(binpath.stem + '.meta')
    assert 'mean_waveforms' not in modules  # Must use catGT data otherwise
    
    # Src ks dir
    ks_dir_src = get_sorting_output_path(
        project, subject, experiment, alias, probe, sorting_analysis_name
    )
    if not dry_run and not ks_dir_src.exists():
        raise FileNotFoundError(ks_dir_src)
    print(f"Kilosort input results dir: {ks_dir_src}")

    # Target ks_dir
    ks_dir = get_sorting_output_path(
        project, subject, experiment, alias, probe, f'{sorting_analysis_name}_{analysis_name}'
    )
    if ks_dir.exists() and not rerun_existing:
        print(f"rerun_existing == False and kilosort dir exists at {ks_dir}...:\n Doing nothing.\n\n")
        return
    elif ks_dir.exists() and rerun_existing:
        print(f"rerun_existing == True: Deleting post-processed kilosort dir at {ks_dir}.\n\n")
        import shutil
        shutil.rmtree(ks_dir)
    print(f"Postprocessing results at: {ks_dir}\n")

    if not dry_run:
        print(f"Copying original ks dir to output dir\n")
        copy_ks_dir(ks_dir_src, ks_dir)
    
    # Generate ecephys_spike_sorting config and save it in output dir
    cfg_path = ks_dir/'postprocessing-input.json'
    json_dir = ks_dir
    kwargs_dict = {k: v for d in params for k, v in d.items()}  # params for all modules in single dict
    KS2ver = get_ks_version(sorting_analysis_name)
    if not dry_run:
        _ = createInputJson(
            str(cfg_path),
            # Directories and data
            input_meta_path=str(metapath),
            continuous_file=str(binpath),  # CatGT (unused)
            npx_directory=str(binpath.parents[3]),  # CatGT (unused)
            extracted_data_directory=str(binpath.parents[3]),  # CatGT (unused)
            spikeGLX_data=True,
            kilosort_output_directory=str(ks_dir),
            ks_make_copy=False,
            KS2ver=KS2ver,
            **kwargs_dict
    )   

    start = datetime.now()
    
    for module in modules:
        output_json = json_dir/(f"{module}-output.json")  
        command = (
            f"python -W ignore -m ecephys_spike_sorting.modules.{module}"
            f" --input_json {cfg_path}"
            f" --output_json {output_json}"
        )
        print(f'Run module {module}:')
        if dry_run:
            print(f'Dry run. Not running: {command}')
        else:
            print(f'Running command `{command}`')
            subprocess.check_call(command.split(' '))
        # !{command}
        print('\n')

    end = datetime.now()
    print(f"{end.strftime('%H:%M:%S')}: Finished {project}, {subject}, {experiment}, {alias}, {probe}.")
    print(f"Run time = {str(end - start)}\n\n")

    return 1


def copy_ks_dir(src, tgt):
    "Copy src to tgt and symlink .dat files."
    import os
    IGNORE = ['.phy']
    ks_dir = Path(src)
    copy_dir = Path(tgt)
    assert not copy_dir.exists()
    os.mkdir(copy_dir)
    for file in [f for f in ks_dir.iterdir()]:
        if file.suffix == '.dat':
            # Symlink all data files
            dest = copy_dir/file.name
            os.symlink(Path('..')/file.parent/file.name, dest)
        else:
            if file.name in IGNORE:
                continue
            # Don't use copytree because chmod raises PermissionError on smb share
            from ecephys.utils import system_copy
            system_copy(file, copy_dir/file.name)


def get_ks_version(sorting_analysis_name):
    try:
        sorter_name, _ = get_analysis_params(
            'sorting',
            sorting_analysis_name 
        )
        if sorter_name == 'kilosort2_5':
            return '2.5'
        elif sorter_name == 'kilosort2':
            return '2.0'
        elif sorter_name == 'kilosort3':
            return '3.0'
        else:
            assert False
    except ValueError:  # Key not found in analysis_cfg.yml
        if 'ks2_5' in sorting_analysis_name:
            return '2.5'
        elif 'ks3_' in sorting_analysis_name:
            return '3.0'
        elif 'ks2_' in sorting_analysis_name:
            return '2.0'
        else:
            assert False
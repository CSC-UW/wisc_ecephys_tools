from pathlib import Path
from datetime import datetime
import subprocess

from ecephys_spike_sorting.scripts.create_input_json import createInputJson
from ecephys_analyses.data import channel_groups, paths, parameters


def run_postprocessing(
    subject, condition,
    sorting_condition, postprocessing_condition,
    catgt_data=True,
    rerun_existing=True
):
    
    print(f"Postprocessing: {subject} {condition} {sorting_condition} {postprocessing_condition}")
    # Modules and associated parameters
    modules = []
    params = []
    module_name_params = parameters.get_analysis_params(
        'ks_postprocessing',
       postprocessing_condition 
    )
    for d in module_name_params:
        modules += d.keys()
        params += d.values()
    
    # Data
    assert catgt_data
    binpaths = paths.get_sglx_style_datapaths(
        subject, 
        condition,
        'ap.bin',
        catgt_data=True,
    )
    # assert len(binpaths) == 1
    if len(binpaths) > 1:
        import warnings
        warnings.warn("Multiple bin files. Recover metadata from first")
    binpath = binpaths[0]
    metapath = binpath.parent/(binpath.stem + '.meta')
    print(f"catGT preprocessed data: {binpath}")
    
    # Src ks dir
    ks_dir_src = paths.get_datapath(
        subject,
        condition,
        sorting_condition,
    )
    if not ks_dir_src.exists():
        raise FileNotFoundError(ks_dir_src)
    print(f"Kilosort input results dir: {ks_dir_src}")

    # Target
    ks_dir = paths.get_datapath(
        subject,
        condition,
        sorting_condition + '_' + postprocessing_condition,
    )
    if (ks_dir/'amplitudes.npy').exists() and not rerun_existing:
        print(f"Kilosort dir exists at {ks_dir}...\n Doing nothing.\n\n")
        return
    print(f"Postprocessing. Results at: {ks_dir}")
    copy_ks_dir(ks_dir_src, ks_dir)
    
    # Save config in ks dir
    cfg_path = ks_dir/'postprocessing-input.json'
    json_dir = ks_dir

    # KS version
    KS2ver = get_ks_version(sorting_condition)
    
    # Params
    kwargs_dict = {k: v for d in params for k, v in d.items()}
    input_json = createInputJson(
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

#     # rerun existing
#     if (output_dir/'spike_times.npy').exists() and not rerun_existing:
#         print(f'Passing: output directory is done: {output_dir}\n\n')
#         return

    print('running')
    start = datetime.now()
    
    for module in modules:
        output_json = json_dir/(f"{module}-output.json")  
        command = (
            f"python -W ignore -m ecephys_spike_sorting.modules.{module}"
            f" --input_json {cfg_path}"
            f" --output_json {output_json}"
        )
        print(f'Running command `{command}`')
        subprocess.check_call(command.split(' '))
        # !{command}

    end = datetime.now()
    print(f"{end.strftime('%H:%M:%S')}: Finished {subject}, {condition}, {sorting_condition}.")
    print(f"Run time = {str(end - start)}\n\n")

    return 1


def copy_ks_dir(src, tgt):
    "Copy src to tgt and symlink .dat files."
    import os, shutil
    IGNORE = ['.phy']
    ks_dir = Path(src)
    copy_dir = Path(tgt)
    if copy_dir.exists():
        print(f"Removing ks dir at {copy_dir}..")
        shutil.rmtree(copy_dir)
    print(f"Copying original ks dir to {copy_dir}\n")
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
            from ecephys.utils.utils import system_copy
            system_copy(file, copy_dir/file.name)


def get_ks_version(sorting_condition):
    sorter_name, _ = parameters.get_analysis_params(
        'sorting',
        sorting_condition 
    )
    if sorter_name == 'kilosort2_5':
        return '2.5'
    elif sorter_name == 'kilosort2':
        return '2.0'
    elif sorter_name == 'kilosort3':
        return '3.0'
    else:
        assert False
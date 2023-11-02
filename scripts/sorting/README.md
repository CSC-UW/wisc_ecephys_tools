# Running spike sorting at WISC

# Overview

1. Package installation
    - ecephys/wisc_ecephys_tools
    - Spikeinterface (CSC-UW fork!)
    - Spikesorter (Vanilla KS2.5 version already installed)
    - For motion estimation: pytorch `https://pytorch.org/get-started/locally/`
1. Project information (-> output file locations)
    - Fill `wis_ecephys_tools/projects.yaml` if you want a custom sorting location
1. Subject information and exclusions
    - Modify/add subject file in `wisc_ecephys_tools/subjects` directory
    - Refresh cache and push updated subject file and cache if all looks good
    - Update/save `{probe}.ap.artifacts.htsv` file in `shared` project's _experiment_subject_ directory.
2. Estimate motion
    - Run initial estimate_motion, with `--optionsPath` and `--prepro_only` 
    options
    - Inspect motion estimates. If unsatisfactory:
        - Prepare output `preprocessing` folder for rerun (WARNING: Ensure the `preprocessing` dir and `opts.yaml` file in the sorting directory remain consistent at all tme)
        - Rerun with `--from_folder` and `--prepro_only` options.
3. Run sorting
4. Curate
5. Run postprocessing and quality metrics
6. Move files / clear drives
    - Delete `recording.dat` (Double check curation is complete and postprocessing went well)
    - Create a `postpro` symlink in the sorting directory to make your postprocessing available as default
    - Move the sorting dir to the `shared_s3` folder

# Installation

You will need three packages properly installed in your spike sorting environment:

1. ecephys: https://github.com/CSC-UW/ecephys
1. wisc_ecephys_tools: https://github.com/CSC-UW/wisc_ecephys_tools
1. CSC-UW fork of spikeinterface, `wisc/sorting` branch: https://github.com/CSC-UW/spikeinterface/tree/wisc/sorting
1. Kilosort


For the former two: check out main READMEs.

## Spikeinterface

For Spikeinterface, we need a couple changes from vanilla spikeinterface, hence the CSC-UW fork.

```bash
conda activate my-sorting-env
git clone https://github.com/CSC-UW/spikeinterface
cd spikeinterface
git checkout wisc/sorting
pip install -e .
cd ..
```

After this you can check your install (Watch for the `Editable project location` line):
```
pip show spikeinterface
```

> Name: spikeinterface  
> Version: 0.98.0.dev0  
> Summary: Python toolkit for analysis, visualization, and comparison of spike sorting output  
> Home-page:  
> Author:  
> Author-email: Alessio Buccino <alessiop.buccino@gmail.com>, Samuel Garcia <sam.garcia.die@gmail.com>  
> License:  
> Location: /home/tbugnon/miniconda3/envs/ecephys_dev/lib/python3.10/site-packages  
> Editable project location: /home/tbugnon/projects/ecephys_dev/spikeinterface  
> Requires: joblib, neo, numpy, probeinterface, threadpoolctl, tqdm  
> Required-by: ecephys  

## Kilosort

A version of KS is already compiled at `/Volumes/scratch/neuropixels/matlab/external/Kilosort-upstream-v2.5`

If you want to use a different sorter/version, it's quite easy thanks to our using SpikeInterface: you can install it (wherever) and make sure that the paths to the install is provided in the sorting options file (see below).

## Pytorch

For motion estimation you need pytorch installed. I tried only with CPU-based version

Check out: https://pytorch.org/get-started/locally/

Typically:

```conda install pytorch torchvision torchaudio cpuonly -c pytorch```

or ```pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu``` (That is new, haven't tried)


# Project information (-> output file locations)


If you want to change the root directory in which sortings are saved, you can add a path in the  `wisc_ecephys_tools/projects/projects.yml` .
This path will used by specifying the `project` name variable in wisc_ecephys_tools routines and scripts.

Currently, the following projects/paths of interest are these:

- `shared`: `/Volumes/npx_nfs/shared_s3` -> Backed up shared location we save the completed sortings (without heavy `recording.dat` preprocessed AP-band files)
- `shared_nobak`: `/Volumes/npx_nfs/nobak/shared` -> Slow drive without backup, suitable to store sorted data awaiting for curation (with their heavy `recording.dat` preprocessed AP-band files)
- `shared_nvme`: `/nvme/neuropixels/shared` -> Fast drive suitable for sorting and curation, and postprocessing/metrics extraction
- `shared_ssd`: `/ssd-raid0/neuropixels/shared` -> Fast drive suitable for sorting, curation, and postprocessing/metrics extraction


The `nvme` and `ssd-raid0` drives are around 5TB each, meaning they can hold one single-probe 48h recording sorting at once. 

You can check available disk space with the `df` shell command.

# Input files and exclusions

## Subject files

The files concatenated during sorting are pulled based on the subject's yaml files found in `wisc_ecephys_tools/subjects`.

For instance:

```yaml
---
recording_sessions:
  - id: 7-10-2021
    ap: /Volumes/ceph-tononi/npx_archive/CNPIX10-Charles/7-10-2021/SpikeGLX/
    lf: /Volumes/ceph-tononi/npx_archive/CNPIX10-Charles/7-10-2021/SpikeGLX/
    imSyncType: barcode
  - id: 7-11-2021
    ap: /Volumes/ceph-tononi/npx_archive/CNPIX10-Charles/7-11-2021/SpikeGLX/
    lf: /Volumes/ceph-tononi/npx_archive/CNPIX10-Charles/7-11-2021/SpikeGLX/
    imSyncType: barcode
experiments:
  novel_objects_deprivation:
    recording_session_ids:
      - 7-10-2021
      - 7-11-2021
    aliases:
      full:
        - start_file: 7-10-2021_g0_t0
          end_file: 7-11-2021_g1_t8
...
```

Here, the `novel_objects_deprivation` experiment is associated to a table of information describing all the AP (or LF) files found in the locations described by the `7-10-2021` and `7-11-2021` `recording_sessions`.

The alias (always "`full`" by default) lets one subset specific files within this table.


## Subject cache

Because indexing of the archive drives might be slow, the experiment tables are by default pulled from a cache file (`wisc_ecephys_tools/subjects/wne_sglx_cache.gz`). This means that **after adding or modifying a subject file, you need to update the cache**, by running ```python wisc_ecephys_tools/subjects/refresh_cache.py```.

Make sure to double check the output of this command

After this, `git checkout` from `wisc_ecephys_tools` should show that the cache (and the subject files) has been modified.

Don't forget to push updates.

## Exclusions

You might want to exclude some bouts from your data, for instance prolonged epochs of zeros which might make kilosort error, or clear artifactual bouts.

The way to go about this is to define exclusion files. For consistency across sortings and aliases, we define exclusions at the level of the whole experiment, and save them in a shared location. Hence, the exclusions should be saved in the `experiment_subject_directory` of the `shared` project: (eg: `/Volumes/npx_nfs/shared_s3/novel_objects_deprivation/CNPIX16-Walter/imec0.ap.artifacts.htsv`) (next to the hypnograms, prb_sync infos, etc).

The expected filename is `<probe>.ap.artifacts.htsv`, and they should be tab-separated as follows:

```
fname	fileStartTime	fileEndTime	type
9-29-2022_g0_t5.imec0.ap.bin	5340.0	7200.0	flat
9-30-2022_g0_t2.imec0.ap.bin	6324.0	6329.0	artifact
9-30-2022_g0_t5.imec0.ap.bin	3200.0	7200.0	flat
9-30-2022_g0_t5.imec0.lf.bin	3200.0	7200.0	flat
```

NB: 
- Even if you don't want to specify exclusions, add an empty `<probe>.ap.artifacts.htsv` file in the expected location anyway, or the pipeline will fail. This is more annoying but less error-prone.
- If you modify exclusions, you should NOT use the `--from_folder` script option, as this will load previously used exclusions/segments rather than recomputing them

#### Summary:

- Modify/add subject file in `wisc_ecephys_tools/subjects` directory
- Refresh cache and push updated subject file and cache if all looks good
- Update/save `<probe>.ap.artifacts.htsv` file in `shared` project's _experiment_subject_ directory.


# Run preprocessing: estimate motion

Now we should be all set to actually run the sorting pipeline. But we probably want to do it in two steps: First estimate drift motion (without running the whole thing), and then when we're happy with the drift estimate (or decide to skip the motion correction step): run the actual sorting.

The general approach is this:
1. Run a first step of preprocessing/motion estimation with sensible default parameters
1. Look at the peak map and estimated motion
1. If unsatisfactory, modify the parameters in the sorting's options file, prepare the output folder for a rerun, and rerun using the options files in the output sorting directory (`--from_folder` option)
1. Repeat until satisfactory
1. Run the actual sorting (`--from_folder` option)

So:

## 1. __Initial motion estimation run__

Here's the command line you might want to use:

```bash
conda activate my-sorting-env; python run_sorting_pipeline.py --projectName shared_ssd --experimentName novel_objects_deprivation --aliasName full --n_jobs 10 --input CNPIX7-Giuseppe,imec1 --optionsPath opts/sorting_chronic_df.yaml --prepro_only 
```

- ```--prepro_only```: Don't run sorting
- ```--optionsPath```: Path to whichever option file, specifying the preprocessing/motion correction params, and the sorter params. In the `opts` directory are sensible defaults for chronic and acute recordings, differing only in the binsize used for motion estimation.
- ```n_jobs```: Could be 20. Mostly for peak detection/localization step. Note that the motion_estimation step is not taking in account n_jobs properly and will BLOW UP CPU use

In the command line output, look out in particular for these lines and make sure that everything looks ok !  (Number of files, included/excluded segments, total duration, etc)


>             Raw SI recording:  
> ConcatenateSegmentRecording: 384 channels - 30.0kHz - 1 segments - 2,522,432,818 samples  
>                              84,081.09s (23.36 hours) - int16 dtype - 1.76 TiB  
>   
>             First segment full path:  
> /Volumes/ceph-tononi/npx_archive/CNPIX7-Giuseppe/12-12-2020/SpikeGLX/12-12-2020_BL_24hs_g0/12-12-2020_BL_24hs_g0_imec1/12-12-2020_BL_24hs_g0_t0.imec1.ap.bin  
>
>             AP segment table:  
>             fname  type  ...  segmentDuration  fileDuration  
>...
>
> 12           12-12-2020_BL_24hs_b_g0_t1.imec1.ap.bin  keep  ...      2219.999994   3600.000000  
> 13           12-12-2020_BL_24hs_b_g0_t1.imec1.ap.bin  flat  ...      1380.000005   3600.000000  
> ...

## 2. Inspecting outputs

You should now see the sorting directory at `<project_dir>/<experiment>/<alias>/<subject>/sorting.<prb>`

If there was motion estimation performed, the `preprocessing` subdirectory will contain `motion*.npz` (motion estimates), `peak_*.npy`(peak and their locations), and `motion_summary.png`:

The top-left plot is the raw peak map, and top right is after motion correction. Bottom left are motion for each of the spatial windows, and bottom right the motion vector along the probe. 

__The goal is to align the dots on the top right plot.__

__If there's some holes or weird epochs in the peak map, it means you might need to define more exclusion and repeat the process__

__Motion on the order of 10um or less peak-to-peak denotes a pesumably very stable recording__ and could justify disabling drift correction altogether (ie: delete/rename `preprocessing` dir and delete `drift_correction` entry from options file in the sorting directory)

If motion estimation is unsatisfactory, here are some parameters of interest that it might be worth playing wit, in decreasing order of importance/frequency
- `bin_duration_s`: Bin size. If too small there might not be enough spikes in each bin for accurate estimaton. If too large motion might be underestimated (and fast transient ignored). If you modify it it might be a good idea to modify `sigma_smooth_s` accordingly
- `win_sigma_um`/`win_step_um`: Width of the y-axis windows. If too large, non-rigid drift will be ignored. If too small there might not be enough spikes in each bin for accurate estimation
- `speed_threshold`: Maximum motion speed between successive batches. If you see spikes in the motion estimates you could try reducing this 
- `margin_um`: Try values < 0 to exclude border channels from the motion estimation, if the edges of the (raw or corrected) peak map look weird
- `detect_threshold`: 5.0 finds a lot of peaks, some of those probably being noise. If the peak map looks a bit messy you could use a higher value, like 7.0 (which is actually SpikeInterface's defalt), but there'll be less spikes to work with.

If all else fails:
- `corr_threshold`
- `time_horizon_s`: Try someting like 360sec instead of `null`

## 3. Rerunning motion estimation.

The different steps of the motion estimation don't take the same duration:
- Peak detection an localization: very slow
- Motion estimaton: Fast enough but very CPU intensive
- Motion cleaning: ~ instant

Because this step is slow, when rerunning a sorting, the `peak_*` and `motion_*` files will be loaded from the preprocessing directory if available. 

In particular, this means that:
- **if you modify the option files in the sorting directory, you need to make sure that the corresponding files are deleted/moved from the preprocessing directory!!!**
- But on the bright side, if you modify motion_estimation parameters (and not peak detection/localization parameters), you can rerun only the motion_estimation step without redoing the very slow peak detection step by deleting the `motion*` files and not the `peak*` files.

In general, if you rerun preprocessing, here's what you need to do:

1. Prepare the output directory 
    1. copy `<sorting_dir>/preprocessing` to `<sorting_dir>/preprocessing.bak`
    1. Copy `<sorting_dir>/opts.yaml` to `<sorting_dir>/preprocessing.bak` so that you keep track of which options were used in the unsatisfactory preprocessing run (in case you want to go back)
    3. Create a new `<sorting_dir>/preprocessing` folder 
    4. Copy from `preprocessing.bak` **only the files that will be identical across runs**. This depends on which parameters you modified:
        - If changing preprocessing steps BEFORE motion estimation, you need to rerun the peaks, and thus the motion etc: copy nothing
        - If changing peak detection/localization parameters (eg `detect_threshold`): you need to rerun the peaks, and thus the motion etc: copy nothing
        - If changing motion estimation parameters (eg `margin_um`, `bin_duration_s`, `win_..`): The peaks will be identical but not the motions: copy `peaks.npy` and `peak_localizations.npy`, but NOT `motion*`
        - If changing only motion cleaning parameters (`sigma_smooth_s`, `speed_thresold`): The peak and raw motion will be identical, not the clean motion: copy `peaks.npy`, `motion_non_rigid.npz` but NOT `motion_non_rigid_clean.npz`.

    That's a bit of a mouthful, but I put a little bash script that does all these steps, preparing a motion rerun (but **assuming identical peak detection**):
    ```bash
    bash prepare_motion_estimation_rerun.sh <path_to_sorting_dir>
    ```

    eg:

    ```bash
    bash prepare_motion_estmation_rerun.sh /ssd-raid0/neuropixels/shared/novel_objects_deprivation/full/CNPIX14-Francis/sorting.imec0
    ```

2. Modify options of interest in `<sorting_dir>/opts.yaml` . Once again: Make sure these option changes are consistent with what you did regarding the preprocessing directory.


5. Rerun `run_sorting_pipeline.py`, with the `--from_folder` option. In this way, the segments/exclusions/files and options will be pulled from the output sorting directory (therefore ```--optionsPath``` argument should not be specifid:

```bash
conda activate my-sorting-env; python run_sorting_pipeline.py --projectName shared_ssd --experimentName novel_objects_deprivation --aliasName full --n_jobs 10 --input CNPIX7-Giuseppe,imec1 --from_folder --prepro_only
```

# Run sorting

After motion is estimated, we can run the full thing by just removing the ```--prepro_only``` option:

```bash
conda activate my-sorting-env; python run_sorting_pipeline.py --projectName shared_ssd --experimentName novel_objects_deprivation --aliasName full --n_jobs 10 --input CNPIX7-Giuseppe,imec1 --from_folder
```

The slow step here is the preprocessing/copying of the raw data into a `recording.dat` file.

NB: 
- You need to make sure that there's enough room on the drive to copy the full recording before running this step
- You also need to make sure the GPU is free. It's unclear exactly how many sortings can be run in parallel but in general:
    - 2 chronic (48h) probes at the same time is too much
    - 1 chronic probe & 1 acute (2h) probe is fine
    - 2 or 3 acute probes at the same time is fine.
You can check current GPU usage with `nvidia-smi`. Note that the preprocessing/motion estimation step can be run in parallel without limitation (except that caused by heavy CPU or Disk-IO usage)


To ensure that kilosort finished properly, you can make sure that the `params.py` file at `sorting_dir/si_output/sorter_output/params.py` is NOT empty. It can happen that the `spike_times.npy` (and others) files exists but is empty if kilosort crashed towards the end.

# Curate

Curation guidelines on lab google drive.

One note: if you move the file, you need to modify the data path in `params.py` accordingly.

# Run postprocessing and quality metrics

Before running postprocessing, you can make sure that all the units were curated by looking at missing fields in the `cluster_group` column in  `<sorting_dir>/si_output/sorter_output/cluster_info.tsv`. After then it will be too late.

Postprocessing consists in the following steps:
- Waveform extraction (slow if on a slow drive, very slow if `recording.dat`  was deleted) -> So better run just after curation, before clearing the `recording.dat` file and moving the sorting
- Various postprocessing (fast)
- Quality metrics (slow-ish) because of PCA-based metrics.

Quality metrics may also be run separately by hypnogram state, if the option file has a `hyp` section. In which case, the script needs to be input the `--hypnogramProject` argument. The hypnogram used will be loaded from `<hypnogramProject_path>/<experiment>/hypnogram.htsv`

There's two default option files in the `opts` folder: `postpro_acute_df` and `postpro_chronic_df`. The only difference is that the acute postprocessing doesn't run metric by hypnogram state. Inversely, for `postpro_chronid_df`, you need to ensure that a hypnogram is available.

## Run: 

You can run the script with eg:

chronic:
```bash
conda activate my-sorting-env; python run_postprocessing_pipeline.py --projectName shared_ssd --experimentName novel_objects_deprivation --aliasName full --optionsPath opts/postpro_chronic_df.yaml --n_jobs 10 --input CNPIX16-Walter,imec0 --hypnogramProject shared
```

acute:

```bash
conda activate my-sorting-env; python run_postprocessing_pipeline.py --projectName shared_ssd --experimentName discoflow-day --aliasName full --optionsPath opts/postpro_acute_df.yaml --n_jobs 10 --input ANPIX94-NotoriousBIG,imec0
```

All postprocessing output will be saved in the `<postpro_opts_filename_root>` (or more generally `postpro_acute_df` subdirectory of the sorting directory). One could run multiple different types of postprocessing for the same sorting

## Check output

The best way to check that all went well is to have a peek at the `summary_plot` subdirectory in the sorting dir. Look at the distribution of values for each metric, and quickly at the unit plots to make sure that the metric/waveforms actually caught real units.


# Move files an clear drive

If the postprocessing was run properly, it is now time to:

- delete the `recording.dat` file:

    ```bash
    rm <sorting_dir>/si_output/sorter_output/recording.dat
    ```

- Make the postprocessing/metrics visible to be loaded by default. (By default the `ecephys` routines search for stuff in the `postpro` subfolder). We do this by creating a symlink:

    ```bash
    cd <path_to>/<sorting_dir>
    ln -sr <postpro_folder_name> postpro
    ```

    eg:

    ```bash
    cd /ssd-raid0/neuropixels/shared/novel_objects_deprivation/full/CNPIX14-Francis/sorting.imec0
    ln -sr postpro_chronic_df postpro
    ```

- Moving the sorting to their final location: Typically in the `experiment_alias_subject` directory of the `shared`` project:

    ```
    mv <sorting_dir> /Volumes/npx_nfs/shared_s3/<experiment>/<alias>/<subject>/
    ```

Voilà !

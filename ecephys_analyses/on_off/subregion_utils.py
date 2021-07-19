import ecephys.units
from pathlib import Path
import numpy as np
import yaml
from ecephys_analyses.data import channel_groups, paths
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks, argrelmin


def get_subregions(
    subject,
    condition,
    sorting_condition,
    region,
    params,
    savefig=True,
):

    ks_dir = paths.get_datapath(subject, condition, sorting_condition)

   # Get clusters
    if region == 'all':
        depth_interval = None
    else:
        depth_interval = channel_groups.region_depths[subject][condition][region]
    print(f"Get subregions for region {region} at {depth_interval}")
    info_all =  ecephys.units.get_cluster_info(ks_dir)
    info = info_all[
        (info_all['depth'] >= depth_interval[0])
        & (info_all['depth'] <= depth_interval[1])
        & (info_all['group'] != 'noise')
        # & (info_all['KSLabel'] == 'good')
    ]
    
    # Find peaks
    if savefig:
        plotdir = paths.get_datapath(subject, condition, 'plots')
        plotdir.mkdir(exist_ok=True)
        figpath = plotdir/f'subregions_{region}_{sorting_condition}'
    peak_depth_ranges = find_peak_ranges(np.array(info.depth), figpath=figpath, **params)

    print(f"Found N={len(peak_depth_ranges)} subregions from cluster depth distribution")


    subregions = {
        f"subregion_{region}_{i}": (int(subregion_range[0]), int(subregion_range[1]))
        for i, subregion_range in enumerate(peak_depth_ranges)
    }

    savepath = subregions_path(subject, condition, sorting_condition, region) 
    print(f"Save regions at {savepath}")
    with open(savepath, 'w') as f:
        yaml.dump(subregions, f)
        
    return subregions


def subregions_path(
    subject,
    condition,
    sorting_condition,
    region,
):
    return paths.get_datapath(subject, condition, f'subregions_{region}_{sorting_condition}')


def find_peak_ranges(data, binsize=20, smoothing_sd=2, prominence=0.1, figpath=None):
    bin_counts, bins = np.histogram(
        data,
        bins=np.arange(min(data), max(data)+binsize , binsize),
    )
    bin_centers = np.array(bins[0:-1]) + binsize
    smoothed_bin_counts = gaussian_filter1d(
        bin_counts, smoothing_sd, output=float,
    )
    
    # Little hack to include peaks at border as well
    # https://stackoverflow.com/questions/56856794/finding-peaks-at-data-borders
    raw_dat = smoothed_bin_counts
    dat = np.array([0] + list(smoothed_bin_counts) + [0])  # Extend on both sides
    peaks_extended, peaks_info_extended = find_peaks(
        dat,
        prominence=max(smoothed_bin_counts) * prominence
    )
    print(peaks_info_extended)
    # Revert to original indices
    peaks = [p - 1 for p in peaks_extended if p < len(dat) - 2]
    if len(dat) - 2 in peaks_extended:  # - 2 for last
        peaks.append(len(smoothed_bin_counts) - 1)
    left_bases = [max(0, p - 1) for p in peaks_info_extended['left_bases']]
    right_bases = [min(p - 1, len(smoothed_bin_counts) - 1) for p in peaks_info_extended['right_bases']]
    # End of the hack
    base_limits = sorted(list(left_bases) + list(right_bases))
    
    peak_range_idx = []
    for i, peak in enumerate(peaks):
        # Deal with edge cases
        if peak == 0:
            peak_range_idx.append((
                0,
                min([lim for lim in base_limits if lim > peak])
            ))
        elif peak == len(smoothed_bin_counts) - 1:
            peak_range_idx.append((
                max([lim for lim in base_limits if lim < peak]),
                len(smoothed_bin_counts) - 1
            ))
        # Regular case
        else:
            peak_range_idx.append((
                max([lim for lim in base_limits if lim < peak]),
                min([lim for lim in base_limits if lim > peak])
            ))
    print(peak_range_idx)
    peak_ranges = [
        (bin_centers[peak_range[0]], bin_centers[peak_range[1]])
        for peak_range in peak_range_idx
    ]

    if figpath:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(bin_centers, smoothed_bin_counts, color='black')
        colors=plt.cm.rainbow(np.linspace(0,1,len(peak_ranges)))
        for i, peak_range in enumerate(peak_ranges):
            ax.plot(bin_centers[peaks[i]], smoothed_bin_counts[peaks[i]], '+', color='red')
            ax.axvline(x=peak_range[0], linestyle='dotted', color='black')
            ax.axvline(x=peak_range[1], linestyle='dotted', color='black')
            ax.axvspan(peak_range[0], peak_range[1], alpha=0.5, color=colors[i])
        plt.title(f'Detected N={len(peak_ranges)} "subregions" based on cluster density peaks', fontsize=16)
        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)
        plt.ylabel('Smoothed cluster density', fontsize=16)
        plt.xlabel('Cluster distance from tip of probe (um)', fontsize=16)
        fig.savefig(figpath)
        plt.show()
    
    return peak_ranges

    

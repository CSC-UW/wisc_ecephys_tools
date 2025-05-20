import dask.array
import xarray as xr

import wisc_ecephys_tools as wet
from ecephys import wne, xrsig
from wisc_ecephys_tools.rats import utils
from wisc_ecephys_tools.rats.constants import SleepDeprivationExperiments


def do_probe(
    subject: str,
    experiment: str,
    probe: str,
    lowcut: float,
    highcut: float,
    filter_order: int = 2,
    shift: int = 10,
    qs: list[int] = [1],
    zarr_file: str = None,
) -> xr.DataArray:
    """
    Get instantaneous power using filter-hilbert for a given probe. The process is:
    1. Open the LFP data, dropping bad channels
    2. Bipolar reference the LFP
    3. Decimate the LFP, possibly in multiple passes.
    4. Filter the LFP in each band
    5. Compute the instantaneous power
    6. Return the instantaneous power

    Args:
        subject: The subject name.
        experiment: The experiment name.
        probe: The probe name.
        shift: The number of channels to shift the LFP by.
        qs: Decimation factorss
        bands: The bands to compute the instantaneous power for.

    Returns:
        The instantaneous power for the given probe.
    """
    s3 = wet.get_sglx_project("shared")
    nb = wet.get_sglx_project("shared_nobak")

    lfp = wne.utils.open_lfps(
        nb,
        subject,
        experiment,
        probe,
        anatomy_proj=s3,
        badchan_proj=s3,
    )

    # assert "acronym" in lfp.coords, "LFP data missing 'acronym' coordinate"
    # assert "structure" in lfp.coords, "LFP data missing 'structure' coordinate"
    # assert all(c in lfp.channel.coords for c in ["acronym", "structure"]), (
    #     "Coordinates must be on channel dimension"
    # )

    lfp = xrsig.bipolar_reference(lfp, shift)
    for q in qs:
        lfp = xrsig.decimate_timeseries(lfp, q)
    nyquist = lfp.fs / 2
    assert highcut <= nyquist, (
        f"Highcut ({highcut} Hz) must be less than or equal to the Nyquist frequency ({nyquist} Hz)."
    )
    assert lowcut > 0, "Lowcut must be greater than 0 Hz"
    lfp = xrsig.butter_bandpass(lfp, lowcut, highcut, order=filter_order)
    analytic = xrsig.hilbert(lfp)
    ipow: xr.DataArray = dask.array.square(dask.array.abs(analytic))
    ipow = ipow.rename("pwr")

    for v in list(
        ipow.coords.keys()
    ):  # Avoid serialization errors when writing to zarr
        if ipow.coords[v].dtype == object:
            ipow.coords[v] = ipow.coords[v].astype("unicode")

    ipow = ipow.chunk({"channel": ipow["channel"].size, "time": "auto"})
    ipow = ipow.chunk(tuple(max(c) for c in ipow.chunks))  # Ensure uniform chunks

    ipow.to_zarr(zarr_file)
    return ipow


def do_all_delta():
    sep = utils.get_subject_experiment_probe_tuples(
        experiment_filter=lambda x: x in SleepDeprivationExperiments
    )
    nb = wet.get_sglx_project("shared_nobak")
    for subject, exp, probe in sep:
        zarr_file = nb.get_experiment_subject_file(exp, subject, f"{probe}.idelta.zarr")
        print(f"Doing {subject}, {exp}, {probe}")
        do_probe(
            subject,
            exp,
            probe,
            lowcut=0.5,
            highcut=4,
            filter_order=2,
            shift=10,
            qs=[10, 2],
            zarr_file=zarr_file,
        )


def do_all_eta():
    sep = utils.get_subject_experiment_probe_tuples(
        experiment_filter=lambda x: x in SleepDeprivationExperiments
    )
    nb = wet.get_sglx_project("shared_nobak")
    for subject, exp, probe in sep:
        zarr_file = nb.get_experiment_subject_file(exp, subject, f"{probe}.ieta.zarr")
        print(f"Doing {subject}, {exp}, {probe}")
        do_probe(
            subject,
            exp,
            probe,
            lowcut=2,
            highcut=6,
            filter_order=2,
            shift=10,
            qs=[10, 2],
            zarr_file=zarr_file,
        )

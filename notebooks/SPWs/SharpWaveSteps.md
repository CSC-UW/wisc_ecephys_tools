SPW steps, for sleep homeostasis expeirments:
- Add experiment to sessions.yaml, channels.yaml, and analysis_paths.yaml
- identify-hippocampus-from-csd.ipynb, to check hippocampal and white matter channels.
- emg-from-lfp.ipynb
- generate-scoring-edf.ipynb
    - generate-sleepscoring-files.ipynb is NOT neccessary if you are using the Desktop launcher (.bat script).
- Score recovery sleep. (YOU DONT HAVE TO DO THIS. WHY?)
- get_spw_detection_params.ipynb
    - You only need to have scored recovery sleep in order to begin this step. (NOT TRUE. WHEN DID THIS CHANGE?)
- generate-CSD-reports.ipynb
    - Requires sharp_wave_detection_params.json
- Begin scoring the rest of the subject's sleep, starting with the light periods
- generate-empty-sr_chans-files.ipynb
- Identify startum radiatum channels for each recording, for manual drift tracking.
- sr_chans-to-datetime.ipynb
    - Requires identifying stratum radiatum channels for each recording.
- get_spws.ipynb
- get-spectrograms.ipynb
- get-bandpower.ipynb
    - get_spectrograms.ipynb may be more appropriate now.
- visbrain-hypnogram-to-datetime.ipynb
    - Requires scoring each recording.

Identifying stratum radiatum channels:
- Minimum CSD variance -> In some states: CA1 inversion, or perhaps slightly ventral.
- Theta trough -> CA1 inversion
- Ripple peak -> 40um above CA1 inversion.
- Ripple trough -> Stratum radiatum, 140um below CA1 inversion.
- Deepest CSD sink "maximum" -> CA1 inversion?

SPW steps, for drug experiments:
- Add experiment to paths.yaml and channels.yaml
- identify-hippocampus-from-csd.ipynb, to check hippocampal and white matter channels.
- emg-from-lfp.ipynb
- generate-scoring-edf.ipynb
    - generate-sleepscoring-files.ipynb is NOT neccessary if you are using the Desktop launcher (.bat script).
- get_spw_detection_params.ipynb
    - You only need to have scored the first two baseline hours in order to begin this step.
- generate-CSD-reports.ipynb
- generate-empty-sr_chans-files.ipynb
- sr_chans-to-datetime.ipynb
    - Requires identifying stratum radiatum channels for each recording.
- get_spws.ipynb
- get-spectrograms.ipynb
- get-bandpower.ipynb
    - get_spectrograms.ipynb may be more appropriate now.
- visbrain-hypnogram-to-datetime.ipynb
    - Requires scoring each recording.
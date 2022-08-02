# #all channel maps are in SpikeGLX user order.
#
# Parameters:
# ===========
# #all:
#   The probe's full channel map in SpikeGLX user order. #all channel numbers are as
#   seen in SGLX. For example, [0] = LF0;384 in the LongColumn map.
# emg_from_lfp:
#    Channels used to derive a virtual EMG.
# superficial_ctx:
#   Visually identified in the LFP during the first 2h of recovery sleep.
# #white_matter:
#   Center of white matter. According to Paxinos and Watson, this should be ~400um
#   from the pyramidal layer, with lower and upper limits of ~266um and ~533um from
#   the pyramidal layer, respectively.
# hippocampus:
#   Identified on the basis of whole-probe CSD during SWRs from the first 2h of
#   recovery sleep.
# drift_tracking:
#   Hippocampal channels, +/- additional channels above and below to #allow for drift.
#   This is probably unnecessary, even for animals with a lot of drift.

# TODO: Remove stratum_pyrmidale_inversion channels, or clarify that they are from the first2h recovery sleep?
# TODO: Fix notes above.





# Depths of structures. Corresponding to depths in Phy.
# WATCH OUT: 0 is tip of probe, not necessarily the deepest channel
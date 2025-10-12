import wisc_ecephys_tools as wet
from ecephys.wne.sglx.utils import load_singleprobe_sorting
from ecephys.wne.siutils import get_quality_metric_filters

# Data
projectName = "shared_s3"
subjectName = "CNPIX12-Santiago"
probe = "imec1"
experiment = "novel_objects_deprivation"

# filters = {
#     "quality": {
#         "good",
#         "mua",
#     },  # "quality" property is "group" from phy curation. Remove noise
#     "firing_rate": (0.0, float("Inf")),  # No need when plotting by depth
#     # ...
# }
# Change levels for single-unit selections etcs
# "conservative"/"intermediate"/"permissive" for each category
df_simple_filters, df_callable_filters = get_quality_metric_filters(
    required_threshold="permissive",
    isolation_threshold=None,
    false_negatives_threshold=None,
    presence_threshold=None,
)

# Plotter
aggregate_spikes_by = "depth"  # "depth"/"cluster_id" or any other property
tgt_struct_acronyms = None  # Plot only target structures, in specific order. eg ["VM", "VL"]

### END USER

sglxSubject = wet.get_sglx_subject(subjectName)
sglx_project = wet.get_sglx_project(projectName)

si_ks_sorting = load_singleprobe_sorting(
    sglx_project,
    sglxSubject,
    experiment,
    probe,
)
si_ks_sorting = si_ks_sorting.refine_clusters(
    simple_filters=df_simple_filters,
    callable_filters=df_callable_filters,
)
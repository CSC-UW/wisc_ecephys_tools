import wisc_ecephys_tools as wet
from ecephys.wne.sglx.utils import load_multiprobe_sorting
from ecephys.wne.siutils import get_quality_metric_filters

# Data
projectName = "shared_s3"
subjectName = "CNPIX12-Santiago"
experiment = "novel_objects_deprivation"
probes = [
    "imec1",
]

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
tgt_struct_acronyms = {"imec1": None}  # Plot only target structures, in specific order. eg ["VM", "VL"]

### END USER

sglxSubject = wet.get_sglx_subject(subjectName)
sglx_project = wet.get_sglx_project(projectName)

multiprobe_sorting = load_multiprobe_sorting(
    sglx_project,
    sglxSubject,
    experiment,
    probes,
)
multiprobe_sorting = multiprobe_sorting.refine_clusters(
    simple_filters_by_probe={prb: df_simple_filters for prb in probes},
    callable_filters_by_probe={prb: df_callable_filters for prb in probes},
)
print(multiprobe_sorting)


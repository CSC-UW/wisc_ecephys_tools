import argparse
import subprocess
import wisc_ecephys_tools as wet
from wisc_ecephys_tools.sortings import get_subject_probe_structure_list
from ecephys.wne.sglx import utils as sglx_utils


# Create a command line argument parser
example_text = """
example:

python pane_per_structure.py experiment "conda activate ecephys && python run_off_detection experiment alias "
python pane_per_structure.py --run experiment "conda activate ecephys && python run_off_detection experiment alias "
python pane_per_structure.py --run --descendants_of Cx experiment "conda activate ecephys && python run_off_detection experiment alias "

This will create several panes (one for each probe) and type (or execute, if the "--run" flag
is specified) in each:
```conda activate ecephys && python run_off_detection experiment alias subjectName,probe,acronym```
"""
parser = argparse.ArgumentParser(
    description=(
        f"Create one pane per completed subject/probe/acronym within "
        f"an existing tmux session and type/run `<command_prefix>+'<subj>,<prb>,<acronym>'`"
        f"in each pane.\n\n"
    ),
    epilog=example_text,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument("--run", action="store_true", help="If present, we run the command in each pane.")
parser.add_argument("experiment", type=str, help="Name of experiment we search sortings for")
parser.add_argument("--descendants_of", required=False, type=str, help="Acronym of atlas structure (eg 'Cx') restricting the returned structures")
parser.add_argument("--min_N_units", required=False, type=int, help="Skip structures with less units", default=0)
parser.add_argument("--min_unit_sumFR", required=False, type=int, help="Skip structures with lower aggregate firing rate", default=0)
parser.add_argument(
    "command_prefix", type=str, help="Command to write in the pane. `'subj,prb,acronym'` is appended for each pane."
)
args = parser.parse_args()

MAX_PANES_PER_WINDOW = 20


# Read the file containing the list of values
subject_probes_structures = get_subject_probe_structure_list(
    args.experiment,
    "full",
    select_descendants_of=[args.descendants_of],
)


# Add space to prefix string if there isn't any
prefix = args.command_prefix
if not prefix.endswith(" "):
    prefix += " "

i = 0
for val in subject_probes_structures:

    # Subselect
    if args.min_N_units > 0 or args.min_unit_sumFR > 0:
        properties = sglx_utils.load_singleprobe_sorting(
            wet.get_sglx_project("shared"),
            wet.get_sglx_subject(val[0]),
            args.experiment,
            val[1]
        ).refine_clusters(
            {"quality": {"good", "mua", "unsorted"}},
            verbose=False,
        ).select_structures(
            [val[2]],
            verbose=False,
        ).properties

        if len(properties) <= args.min_N_units:
            continue
        if properties.fr.sum() <= args.min_unit_sumFR:
            continue

    if not (i + 1) % MAX_PANES_PER_WINDOW:
        subprocess.run(f"tmux new-window", shell=True)

    pane_i = (i+1) % MAX_PANES_PER_WINDOW

    # Split the current pane into a new pane and run a command in it
    subprocess.run(f"tmux split-window", shell=True)
    subprocess.run("tmux select-layout even-vertical", shell=True)

    # Format tuple to remove parenthesis/space
    suffix = str(val).replace("(", "").replace(")", "").replace(" ", "")

    if args.run:
        # Append the value to the command line and execute it
        subprocess.run(f"tmux send-keys -t {pane_i} '{prefix}{suffix}' Enter", shell=True)
    else:
        # Append the value to the command line without executing it
        subprocess.run(f"tmux send-keys -t {pane_i} '{prefix}{suffix}'", shell=True)

    i+=1
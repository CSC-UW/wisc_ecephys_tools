import subprocess
from datetime import datetime
from pathlib import Path
from ecephys_analyses.data import paths
from ecephys_analyses.data.channel_groups import full_names
from ecephys.data.paths import parse_sglx_stem

from ecephys.sglx.cat_gt import get_catGT_command


CATGT_PATH = "/Volumes/scratch/neuropixels/bin/CatGT-linux/runit.sh"

CATGT_CFG_BASE = {
    'aphipass': 300,
    'aplopass': 9000,
    'gbldmx': True,
    'gfix': '0.40,0.10,0.02',
}  # Default dict applied to all

SYNC_CHANNEL = 384  # Applied to all

AP = True
LF = False

CATGT_CFG_MANDATORY_KEYS = [
    'g', 't', 'prb',
    'aphipass', 'aplopass', 'gbldmx', 'gfix'
]

SRC_ROOT_KEY_DF = 'raw_chronic'
TGT_ROOT_KEY_DF = 'catgt'


def run_catgt(run_specs, dry_run=True, src_root_key=SRC_ROOT_KEY_DF, tgt_root_key=TGT_ROOT_KEY_DF):
    """
    Args:
        run_specs (list): List of (<subject>, <condition>, <exp_id>, <run_id>, <catgt_cfg>) tuples.
            CatGT output is saved with probe-folder structure at roots_paths[<tgt_root_key>]/subject/condition/exp_id

    """
    subject, condition, exp_id, run_id, catgt_cfg = run_specs
    
    assert all([key in catgt_cfg for key in CATGT_CFG_MANDATORY_KEYS])
    
    src_dir = paths.get_subject_root(subject, src_root_key)/exp_id
    dest_dir = paths.get_subject_root(subject, tgt_root_key)/condition/exp_id
    
    cmd = get_catGT_command(
        catGT_path=CATGT_PATH,
        wine_path=None,
        dir=str(src_dir),
        dest=str(dest_dir),
        run=run_id,
        ap=AP,
        lf=LF,
        SY=f"{catgt_cfg['prb']},{SYNC_CHANNEL},6,500",
        prb_fld=True,
        out_prb_fld=True,
        **catgt_cfg,
    )

    start = datetime.now()
    print(f"Running {cmd}")
    if dry_run:
        print("Dry run: doing nothing")
    else:
        dest_dir.mkdir(parents=True, exist_ok=True)
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    end = datetime.now()

    print(f"{end.strftime('%H:%M:%S')}: Finished {subject}, {run_id}. Run time = {str(end - start)}")


def get_run_specs(subject, condition_group, catgt_cfg=None, rerun_existing=True):
    """Return list of (<subject>, <condition>, <exp_id>, <run_id>, <catgt_cfg>) tuples.

    The following keys are added to catgt_cfg for each run: 't', 'g', 'prb', 

    Examples:

        >>> get_run_specs('Valentino', 'eStim')
        [
            ('CNPIX3-Valentino', 'eStim_condition_1', '2-19-2020', '2-19-2020',    {'g': '1', 'prb': '0', 't': '4,4',}), 
        ]
    """
    if catgt_cfg is None:
        catgt_cfg = CATGT_CFG_BASE
    else:
        assert all([k in catgt_cfg for k in ['aphipass', 'aplopass', 'gbldmx', 'gfix']])
    
    assert LF == False or rerun_existing  # Rerun logic only checks ap.meta

    conditions = paths.get_conditions(subject, condition_group)
    datapath_dict = paths.load_datapath_yaml()
    all_run_specs = []
    for cond in conditions:
        if not rerun_existing:
            output_ap_meta = paths.get_sglx_style_datapaths(
                subject, cond, 'ap.meta', catgt_data=True
            )
            if not len(output_ap_meta) == 1:
                raise ValueError(f"Multiple output meta files for {subject} {cond}."
                                 f"Only run catgt on non-combined conditions")
            if output_ap_meta[0].exists():
                print(f"Rerun=False: pass {subject} {cond}", end="")
                print(f"(found ap.meta at {output_ap_meta[0]}")
                continue
        cond_spec = datapath_dict[subject][cond]
        # # Name
        # full_name = full_names[subject]
        # exp
        assert len(list(cond_spec.keys())) == 1
        exp = list(cond_spec.keys())[0]
        # run
        stems = cond_spec[exp]
        runs, gates, trigs, probes = zip(*[
            parse_sglx_stem(stem) for stem in stems 
        ])
        assert len(set(runs)) == 1  #TODO
        assert len(set(probes)) == 1  #TODO
        assert len(set(gates)) == 1  #TODO
        sorted_trigs = sorted([int(t.split('t')[1]) for t in trigs])
        trg_str = ','.join([str(t) for t in sorted_trigs])  # "0,1,2,8" or "0"
        run, gate, trig, probe = parse_sglx_stem(stems[0])
        all_run_specs.append(
            tuple([subject, cond, exp, run, {
                'g': gate.split('g')[1],
                'prb': probe.split('imec')[1],
                't': trg_str,
                **catgt_cfg,
            }])
        )
    print("...")
    return all_run_specs

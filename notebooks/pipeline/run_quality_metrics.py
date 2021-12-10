#!/usr/bin/env python
# coding: utf-8

# In[ ]:


get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')


# In[ ]:


from ecephys_analyses.data import paths
from ecephys_analyses.sorting.postprocessing import run_postprocessing


# In[ ]:


## USER

# ks_sorting_condition = 'ks2_5_catgt_Th=12-10_lam=50_8s-batches_postpro_1'
ks_sorting_condition = 'ks2_5_catgt_Th=12-10_lam=50_8s-batches_postpro_2'

postprocessing_condition = 'metrics_all_isi'

##########
## Manual:
# Subject, condition
data_conditions = [
    # ('Doppio', 'sleep-homeostasis-2h_imec0'),
#     ('Eugene', '10-19-2020_NREM_depth1.5_imec0'),
]
##########
## Auto

condition_groups = [
#     # ('Allan', 'SD'),
#     # ('Doppio', 'SD'),
#     # ('Luigi', 'SD'),
    # ('Charles', 'SD'),
    # ('Doppio', 'SD'),
    # ('Allan', 'SD'),
    ('Adrian', 'SD'),
#     ('Alessandro', 'SD'),
#     ('Segundo', 'SD'),
#     # ('Charles', 'eStim'),
]

data_conditions = []
for subject, condition_group in condition_groups:
    data_conditions += [
        (subject, cond)
        for cond in paths.get_conditions(subject, condition_group)
    ]
print(f'Data condition N={len(data_conditions)} (Looks good?): {data_conditions}')

#########

# src_root_key = condition_groups[0][1]  # Where we find the sorting. A key in roots.yml
src_root_key = 'SD'  # Where we find the sorting. A key in roots.yml

#########


n_jobs = 1  # Don't parallelize (possibly messed up tmp directories?)
assert n_jobs == 1

## end USER


# In[ ]:


for (subject, condition) in data_conditions:
    print(subject, condition, ks_sorting_condition, postprocessing_condition)
    run_postprocessing(
        subject,
        condition,
        ks_sorting_condition,
        postprocessing_condition,
        root_key=src_root_key,
        rerun_existing=False
        # rerun_existing=True
    )


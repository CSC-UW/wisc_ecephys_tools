Example 1:

Create pane for each dorsal thalamic area and run MU-based spindle detection, save results in seahorse project:

```bash
conda activate myenv
python pane_per_structure.py --run --descendants_of Thal-D novel_objects_deprivation full "conda activate myenv; python run_mu_spindles_detection.py novel_objects_deprivation full seahorse"
```

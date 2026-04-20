# AGENTS.md — wisc_ecephys_tools

## What This Is

WISC-specific infrastructure for extracellular electrophysiology. Depends on local data organization, hardware, and NFS mounts. Generic code belongs in `ecephys`; WISC-specific code belongs here.

**Version:** 0.1.1 | **Python:** >=3.9 | **No CLI entry points** | **No test suite**

## Build

```bash
# Install (editable, from workspace root)
cd gfys_workspace && uv sync --all-extras --group dev

# Linting
uv run ruff check src/
```

## Package-Level Convenience Functions

The most commonly used entry points, exported from `wisc_ecephys_tools`:

```python
import wisc_ecephys_tools as wet

# Load a project (cached, LRU 8)
project = wet.get_sglx_project("offproj")
project.dir  # → Path("/Volumes/npx_nfs/nobak/offproj")

# Load a subject (cached via parquet)
subject = wet.get_sglx_subject("CNPIX12-Santiago")
subject.get_experiment_names()
subject.get_experiment_probes("novel_objects_deprivation")

# Shared project shortcut
shared = wet.get_shared_project()  # → shared_nobak project
```

## Module Structure

| Module | Purpose |
|--------|---------|
| `projects/projects.py` | `get_sglx_project(name)`, `get_wne_project(name)` — cached project loading |
| `projects/projects.yaml` | Project definitions: name → mount point mappings |
| `subjects/subjects.py` | `get_sglx_subject(name)`, `get_subject_library()` — cached subject loading |
| `subjects/*.yml` | 55 subject YAML files (ANPIX, CNPIX, ACR, SST prefixes) |
| `subjects/wne_sglx_cache.pqt` | Parquet cache of subject metadata (auto-refreshed) |
| `core.py` | `get_shared_project()` |
| `constants.py` | `Files` enum |
| `rats/` | CNPIX rat-specific utilities (see below) |
| `ephyviewer_app/` | Interactive spike sorting viewer GUI |

## Projects

Defined in `projects/projects.yaml`. Each entry maps a short name to an absolute path:

```yaml
---
project: offproj
project_directory: /Volumes/npx_nfs/nobak/offproj
```

See `gfys_workspace/docs/DATA.md` for the full project list.

### Adding a new project

1. Add an entry to `projects/projects.yaml`
2. The project is immediately available via `wet.get_sglx_project("name")`

## Subjects

55 YAML files in `subjects/`, one per animal. Subject names: `CNPIX{N}-{Name}`, `ANPIX{N}-{Name}`, etc.

Each YAML defines:
- `recording_sessions`: paths to raw SpikeGLX data on NAS
- `experiments`: experiment definitions with aliases and probe configurations
- Probe metadata: channel maps, internal references

### Adding a new subject

1. Create a YAML file in `subjects/` following the existing format
2. Run `subjects/refresh_cache.py` to update `wne_sglx_cache.pqt`
3. The subject is immediately available via `wet.get_sglx_subject("name")`

## Rats Module

Specialized utilities for CNPIX chronic Neuropixels subjects in sleep deprivation experiments.

| Submodule | Purpose |
|-----------|---------|
| `rats/constants.py` | `SleepDeprivationExperiments` enum (NOD, COW, CTN) |
| `rats/utils.py` | `is_valid_cnpix_subject_name()`, subject-experiment-probe tuples |
| `rats/exp_hgs.py` | Hypnogram slicing: day1/day2, light/dark periods, NOD periods |
| `rats/cnd_hgs.py` | Subject-probe-structure lists with BrainGlobe atlas filtering |
| `rats/sortings.py` | `get_subject_probe_list()` — sortings with hypnogram+anatomy requirements |
| `rats/pipeline/` | Data processing steps (hypnogram consolidation, power extraction, condition hypnograms) |

## NFS Mount Requirements

Most operations require NFS mounts to be active:

- `/Volumes/npx_nfs/` — primary NFS (shared, shared_nobak, offproj, seahorse)
- `/Volumes/ceph-tononi/` — CephFS (Tom's projects)
- `/Volumes/scratch/` — scratch space (samoffs)
- `NeuropixelNAS1`, `NeuropixelNAS2` — raw recording archives

If these are not mounted, project/subject loading will succeed but data access will fail with `FileNotFoundError`.

## See Also

- Root `AGENTS.md` — workspace overview, code style
- `ecephys/AGENTS.md` — core library this package builds on
- `gfys_workspace/docs/DATA.md` — data hierarchy, project list, subject schema
- `gfys_workspace/docs/COMPUTE_SERVERS.md` — server specs and mount points

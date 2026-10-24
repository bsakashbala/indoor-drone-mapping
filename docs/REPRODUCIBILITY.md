# Verification and reproducibility

## What was checked for the public package

On 24 October 2026, the public V1 copy was checked with a new virtual environment using Python 3.12.14 on Windows. Dependencies were installed from the original requirements, then frozen into `requirements-lock.txt`:

| Package | Checked version |
|---|---|
| coppeliasim-zmqremoteapi-client | 2.0.4 |
| Pillow | 13.0.0 |
| pyzmq | 27.2.0 |
| cbor | 1.0.0 |

The environment checker successfully imported the four packages and Tkinter and located the two scenes. **All 17 original unit tests passed.** The read-only evidence validator recomputed the committed CSV reading counts, one-metre ray limits and open-interior cell counts and matched the saved summary.

An additional offline partition run completed at **259.10 simulated seconds**, with **20,732 analytic ray readings**, no reported failure and 28 navigation plans. This was a new analytic kinematic check of the public copy, **not a new physics flight**. Its generated files remain in the ignored local `output/` directory. Analytic contact flags and constant height do not constitute a dynamics or hardware safety test.

The public-package preparation changes the computer-specific launcher fallback and removes a local `.deps` import shortcut. It does not change the V1 mapping, planner, scene geometry or low-level controller. New helper tools check the environment, read the recorded evidence and build a ZIP from tracked files. The existing 17 tests remain unchanged; no additional passing-test count is claimed.

## Original physics evidence

The files in `examples/recorded_runs/empty` and `partition` are copied from the earlier V1 validation runs, not regenerated or edited to match the README. The associated summary reports:

| Metric | Empty | Partition |
|---|---:|---:|
| Completed | true | true |
| Simulated duration | 182.75 s | 422.50 s |
| CSV readings | 14,620 | 33,800 |
| Contacts | 0 | 0 |
| Minimum body surface clearance | 0.3433097635 m | 0.3015703218 m |
| Evaluated open-interior cells | 5,776 | 5,596 |
| Unknown evaluated cells | 0 | 0 |
| Maximum range | 1 m | 1 m |

The earlier experiments used CoppeliaSim Edu 4.10.0 and its built-in Quadcopter. The true collision/distance monitors provide evaluation and stop information. They do not supply hidden obstacle rectangles to the planner.

## Evaluation region

For cell-centre coordinates `(x, y)`, the open-interior check includes `abs(x) < 1.9` and `abs(y) < 1.9`. In the partition case it excludes `-0.85 < x < -0.55` with `y < -0.4`, accounting for the partition and a surface margin. This is a defined test region, not a whole-map percentage. It excludes exterior pixels, the outer-wall band and the solid partition.

The boundary-recall metric in `mapping.py` is a different metric: it checks expected room-boundary cells with one-cell tolerance. It is not precision, localization accuracy or proof that all interior space was observed.

## Reproduce the checks

From the repository root, after setup:

```powershell
.\.venv\Scripts\python.exe tools/check_environment.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tools/validate_recorded_runs.py
.\.venv\Scripts\python.exe run.py --offline --no-gui --layout partition --output output/reproduce-offline
```

For a new dynamics run, open the empty or partition scene in the tested simulator, leave it stopped and use:

```powershell
.\.venv\Scripts\python.exe run.py --no-gui --output output/reproduce-physics
```

Confirm `mode`, `completed`, `failure`, `collision_events` and the sensor range in the new metrics. Compare a like-for-like scene and evaluator; do not expect identical wall-clock time or blindly substitute a later simulator/model release.

## Packaging and automation limits

The GitHub Actions workflow runs unit tests and committed evidence checks on Python 3.10 and 3.12. During publication, the first run passed the Python 3.12 checks but found that Pillow 13 requires Python 3.11 or newer. The lock file therefore selects Pillow 12.0.0 for Python 3.10 and Pillow 13.0.0 for newer Python. Both pins satisfy their upstream Python requirements. Current GitHub checks provide the Linux verification for those two branches; local validation used Windows/Python 3.12. The workflow uses the current v7 checkout and Python-setup actions and deliberately does not install CoppeliaSim or claim new physics validation.

This repository is a student demonstration with exact pose, ideal rays, static test layouts and a known work area. Coverage completion, sensing realism and collision avoidance require broader experiments before general claims are appropriate.

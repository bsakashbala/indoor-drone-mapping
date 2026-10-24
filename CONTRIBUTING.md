# Contributing

We welcome clear student experiments, reproducibility fixes and documentation improvements.

1. Reproduce the baseline using the README.
2. Create a branch for one change and explain the problem it addresses.
3. Run `python -m unittest discover -s tests -v` from the project root.
4. Run `python tools/validate_recorded_runs.py` to check committed evidence.
5. For mapping/navigation changes, run an offline check and a separate CoppeliaSim experiment when available. State which you actually ran.
6. Keep generated runs in `output/`, not mixed into baseline evidence. Share new evidence under a clearly named example only when useful.
7. Submit a pull request explaining behaviour, validation and remaining limits. Do not claim hardware validation from analytic or simulator results.

Keep original authorship notices for upstream models/controllers. Do not add simulator installers, virtual environments, credentials, personal account details or unrelated coursework. Report version and scene details when opening a bug. Describe expected/actual behaviour and include relevant metrics rather than a large environment dump.

Do not change committed baseline measurements merely to make a test pass. If a new experiment differs, preserve it as a new case and explain the difference.

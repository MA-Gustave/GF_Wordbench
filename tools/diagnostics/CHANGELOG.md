# Changelog

## 0.1.1

- Force `python.exe` for child CLI, test, and repository-check commands when the GUI runs under `pythonw.exe`.
- Display bounded failing-command output directly in the GUI/headless launcher log.
- Fix the N03 inline CLI parser probe indentation.
- Restrict Ruff to Wordbench-owned Python surfaces (`src`, `tests`, `scripts`).
- Preserve the complete command output in per-step artifact logs.


## 0.1.0

- Initial GF Wordbench mini diagnostic suite.
- Added graphical and headless execution.
- Added environment, repository, contracts, runtime smoke, and release levels.
- Added structured JSON/TXT reports and retained command logs.

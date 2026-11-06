# WordBench Practical Qualification — Desktop Integration v1.1

**Status:** developer integration, candidate-only. **Date:** 2026-11-05.

## Single responsibility

The main Qt GUI (`src/gf_wordbench/entrypoints/gui/window.py`) exposes an
explicit **Practical Qualification…** button and **Run** menu item.
`runtime.py` routes the intent to `practical_tool.py`, which locates the
repository-root `.pyw` and starts a separate Python interpreter. The Qt shell
never imports Tkinter or starts GF. No new validation engine is introduced.

The `.pyw` is a frontend for `gf_wordbench.practical.batch`, with preflight
before `smoke` or `full`. It checks the exact 15 required capabilities and
excludes the five optional capabilities, regardless of selection. The running
campaign is owned by the detached window, including cancellation and logs.

## Default language scope

The 14 focus languages are: `Eng Fre Spa Ger Dut Swe Dan Nor Nno Fin Est Afr
Ita Por`, corresponding to the bounded set in `practical.review14.FOCUS14`.
They were chosen because they produced all 15 *candidates* in the evidence
campaign. Neither membership nor preflight constitutes human certification.

`Sqi Cze Pol Rus Hrv Gre` remain available via **20 pilotes** and through the
CLI for diagnostics, but are not automatically included in the default
campaign. Non-prepared RGL languages are displayed as inventory only.

## Runtime requirements and limitations

- Main Qt application: installed PySide6 and resolved language context.
- Detached qualifier: Python 3.11+ with Tkinter and the repository-root `.pyw`.
- Actual GF execution: GF 3.12, RGL sources and the WordBench practical pilots.
- If the standalone `.pyw` or batch module is missing, the Qt application
  reports the problem rather than running a second implementation.
- If a main-window scan is active, the qualifier action is disabled; a
  separately launched campaign keeps its own lifetime and does not inherit
  the Qt window's cancellation.
- `check` runs without GF. `smoke` runs one required scenario per language.
  `full` runs fifteen required scenarios per language (210 probes for 14).
- Reports stay candidate-only. No canonical gold, publication, RuntimeSet
  activation or human review approval is performed automatically.

## Windows verification

1. Launch `launch_gui.bat` after selecting a language in normal WordBench.
2. Use **Run → Practical Qualification…**; the same operation must be
   reachable from the new toolbar button.
3. Confirm that the 14-focus selection appears, and the other six remain
   selectable via **20 pilotes**.
4. Run **Vérifier** first; GF must not start.
5. Run **Full** only when GF and RGL are available. Verify `languages_unattempted=0`,
   14 requested languages and exactly 210 expected probes in the batch summary.
6. Review the raw outputs independently. A successful `full` is not a
   linguistic certification.

## Tests

- `tests/unit/practical/test_practical_campaign_ui.py`: scope and selected
  language behavior, command construction, preflight and safety.
- `tests/unit/practical/test_practical_tool_launcher.py`: standalone launcher
  resolution, safe interpreter selection and missing-tool behavior.
- `tests/integration/gui/test_main_runtime_composition.py`: Qt action, menu,
  button and inactive-while-scanning behavior (requires PySide6).

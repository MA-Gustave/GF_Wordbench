# Practical multilingual qualification — Windows graphical launcher

**Tool:** `Qualification_Langues_Utiles.pyw` (also available in the main Qt application)  
**Scope:** `practical_generation_v1` — 15 required practical capabilities  
**Status:** candidate GF probes, **not** a linguistic certification or a published RuntimeSet

## Purpose

This GUI is a thin launcher for the existing `gf_wordbench.practical.batch` module. It neither implements GF compilation nor defines a second validation engine. It never writes to the RGL or to the checked-in pilot sources.

The GUI loads the **prepared pilot languages** from `pilots/practical_generation_v1/language_catalog.json` and checks the scope in `profiles/practical_generation_v1.json`. The current supplied catalog contains 20 prepared languages, and their manifests contain 15 required scenarios each. The interface can also *detect* additional `SyntaxXXX.gf` files under `gf-rgl/src/api`, but **does not attempt to qualify those additional languages**: a language requires a prepared, locked WordBench pilot before it can be executed.

## Practical scope

| Domain | Required semantic scenario IDs |
| --- | --- |
| Facts and temporal reference | `factual-present`, `past-event`, `past-state`, `future-reference`, `factual-negation` |
| Relations and attribution | `temporal-order`, `condition-real`, `possibility`, `source-attribution` |
| Data and location | `quantity`, `location` |
| Procedural | `instruction`, `prohibition`, `obligation`, `conditional-instruction` |

The five **optional** capabilities — `anteriority`, `process-ongoing`, `passive-or-rephrase`, `counterfactual`, and `habitual` — are deliberately excluded. A language may realize a semantic scenario in its own grammatical way: the launcher never forces a complete verb-tense inventory.

If the profile is changed to introduce an additional required capability, remove one of the agreed capabilities or alter a pilot's 15-scenario manifest, the GUI blocks execution until its scope is reviewed. Actual scenario SHA-256 validation is delegated to the WordBench preflight command.

## Requirements

- Windows with Python 3.11+ and Tkinter (standard Python installation), and `.pyw` file association.
- GF WordBench repository containing `src/gf_wordbench/practical/batch.py`, the practical profile and the prepared pilots.
- For `smoke` and `full`: a working `gf.exe` (e.g. GF 3.12 Windows) and the checked-out RGL sources.
- Write permissions to a **results directory outside** WordBench, RGL and the GF installation.
- The Python dependencies expected by the installed WordBench release.

## Install and start

**Recommended:** open GF WordBench's main Qt GUI (`launch_gui.bat`), then use
**Run → Practical Qualification (15 capabilities)…** or the **Practical
Qualification…** button next to Run Scan. This opens the separate Tkinter
window without importing Tkinter into the Qt application. The action is
unavailable while an ordinary WordBench scan is in progress. The detached
window owns its own campaign lifecycle and cancellation.

**Alternative:** double-click `Qualification_Langues_Utiles.pyw` in the
**root** of `GF_Wordbench`, next to `Lancer_Campagne_Multilingue.bat`. The application can also find the default `C:\mycode\Grammatical-Framework\GF_Wordbench` repository if launched from Downloads.

Default locations:

```text
WordBench C:\mycode\Grammatical-Framework\GF_Wordbench
GF        C:\mycode\Grammatical-Framework\gf-3.12-windows\gf.exe
RGL       C:\mycode\Grammatical-Framework\gf-rgl
Results   %USERPROFILE%\Downloads\Ars_Magna_Defluens\practical_pilot_runs
```

Adjust paths with the `…` buttons if needed. The default **per-probe time limit is 90 seconds** and the default **overall scheduling limit is 600 minutes**. These are limits, not predicted run times. They may be reduced. In the batch module, the overall limit is checked between languages; remaining languages may not be started when the budget is exceeded.

## Buttons and workflow

1. **Détecter:** reload the prepared pilot catalog and the RGL inventory. The 14-language focus (`Eng Fre Spa Ger Dut Swe Dan Nor Nno Fin Est Afr Ita Por`) is selected by default **only where pilots are present and conforming**. The **14 retenues** button restores that selection; **20 pilotes** explicitly selects every complete prepared pilot, including the six with known technical failures. User selection is still possible. A missing focus pilot is not silently substituted.

   The 14-language focus means 15/15 *technical candidates* in the observed
   campaign, **not** 14 certified languages.
2. **Vérifier les profils:** run `python -m gf_wordbench.practical.batch check --languages ...`. This validates the locked scripts and inputs without starting GF.
3. **Smoke:** run the same preflight automatically, then `run --mode smoke` (the single `factual-present` probe per selected language).
4. **Full:** run the same preflight automatically, then `run --mode full` (15 required scenarios per selected language), with a confirmation dialog.
5. **Arrêter la campagne:** request interruption of the Python process tree (including GF subprocesses on Windows). Interrupted runs may have only partial JSON reports and no global ZIP.
6. **Journal & verdict:** show process output in a separate tab. You can save this live journal. The authoritative evidence remains the WordBench report directory.
7. **Ouvrir les résultats / Ouvrir le ZIP produit:** inspect the output folder or the latest ZIP created by this UI session. The application does not silently reuse an earlier ZIP.

The actual command is constructed as an argument list and started **without shell interpolation**; the subprocess runs with `PYTHONPATH` pointing to WordBench's `src` directory.

## Run results

A completed full campaign produces, when archiving succeeds:

```text
practical_pilot_runs/
  defluens-batch-full-<run-id>/
    batch_summary.json
    batch_summary.csv
    README.txt
    languages/
      ... per-language pilot_run.json, review_template.json, scenario logs ...
  defluens-batch-full-<run-id>.zip
```

The global ZIP contains portable candidate reports and logs, not canonical WordBench `summary.json` + verified manifest evidence. **Do not present that ZIP to Observatory as a qualified canonical WordBench run.** It can be used to study real GF outputs and prepare the missing adapter and human-review work.

Verify `totals.languages_unattempted == 0` in `batch_summary.json` before calling the campaign exhaustive. An exit code of 0 or the status `candidate_for_review` does not mean that a sentence is linguistically approved. No `ready`, gold approval, RuntimeSet release or activation occurs.

## Safety and failures

- Read-only access to the WordBench practical profile and locked pilot inputs.
- No execution if required capability scope drifts, a selected pilot is missing, the RGL module is missing or `gf.exe` is absent.
- Outputs cannot be written inside WordBench, RGL or the GF installation; the CLI also enforces its own protection.
- Preflight failure blocks GF.
- Cancellation stops the child process tree; inspect `batch_summary.json` to identify incomplete work.
- Generated candidate sentences require a separate linguistic human review.

## Verification performed for this GUI build

- The actual `gf_wordbench.practical.batch check` command passed for all 20 pilot languages in the supplied WordBench source snapshot. Each declared 15 scenarios, without executing GF.
- 16 isolated tests cover scope drift, CLI argument composition, output protection, unavailable languages and incomplete results.
- The `.pyw` was opened under a graphical test display, and its `check` button completed the 20-language preflight.
- **GF full/smoke execution on Windows was not performed in the build environment**; the user must validate it on the Windows GF installation.

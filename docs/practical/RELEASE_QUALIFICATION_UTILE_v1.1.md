# WordBench practical qualification — v1.1 main-window integration

**Release type:** source patch for Windows WordBench snapshot dated 2026-11-05.
The core GF implementation, RGL grammars, semantic plans and golden files are unchanged.

## Changes

- A **Practical Qualification…** button is visible beside Run Scan in the main
  PySide6 window, with a matching **Run** menu item.
- The action opens the existing standalone Tkinter `Qualification_Langues_Utiles.pyw`
  with the correct Python interpreter and WordBench working directory. No
  second GF or validation engine has been introduced.
- While a standard WordBench scan is active, the qualifier launcher is disabled.
  An existing detached qualifier window remains an independent process.
- The standalone UI now selects the 14 candidate-focus languages by default:
  `Eng Fre Spa Ger Dut Swe Dan Nor Nno Fin Est Afr Ita Por`.
- The **14 retenues** and **20 pilotes** buttons let users restore the focus
  subset or explicitly include six technically problematic pilot languages.
- All modes still preflight the 15 fixed required practical scenarios; the
  five optional capabilities remain excluded. Extra RGL languages without
  prepared pilots remain inventory only.
- The UI and report wording distinguish *GF candidate generation* from
  human linguistic approval, golden acceptance and publication.

## Validation evidence

- `python -m gf_wordbench.practical.batch check --languages Eng Fre Spa Ger Dut Swe Dan Nor Nno Fin Est Afr Ita Por` returned `ok=true` for all 14 selected pilot languages, with 15 scenarios each, without GF.
- Targeted source-unit tests: **44 passed**, **1 long full-campaign simulation deselected**.
- `python -m compileall` passed for updated Python sources.
- Tests that instantiate the main Qt window are included but **not executed**
  in the build container, where PySide6 is unavailable.
- A real GF Windows full run has **not** been repeated for this UI patch.

## Installation

Unpack the `*_PATCH_C_mycode.zip` archive into
`C:\mycode\Grammatical-Framework` with overwrite enabled. The archive contains
`GF_Wordbench/` as its top-level folder. Back up local modifications first.

## Usage

1. Launch `GF_Wordbench\launch_gui.bat` using the existing WordBench environment.
2. In the main window choose **Run → Practical Qualification…**, or press the
   new button beside **Run Scan**.
3. Check the 14 selected pilot languages and choose **Vérifier** first.
4. Optionally run **Smoke**, then **Full**. The latter runs up to 14×15=210
   required probes, without selecting the five optional ones.
5. Open the resulting batch ZIP. It contains **candidate evidence only**.

**No GF compiler, source grammars, RGL files, goldens, RuntimeSets or external
repositories are modified by this patch.**

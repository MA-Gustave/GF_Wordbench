# Defluens v0.6 — isolated practical GF probe

A single capability in a single language is executed through the existing
`gf_wordbench.practical.pilot.run_pilot`, against the **locked WordBench sources**.
This is not an alternative compiler, grammar source, SA realizer, conformance
result, language release, or claim of linguistic quality.

The native Windows tool remains the `gf.exe` installed at
`C:\mycode\Grammatical-Framework\gf-3.12-windows\gf.exe`.

Example:

```powershell
cd C:\mycode\Grammatical-Framework\GF_Wordbench
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python tools\preview_defluens_capability.py `
  --language Fre --capability factual-negation `
  --gf-executable C:\mycode\Grammatical-Framework\gf-3.12-windows\gf.exe `
  --rgl-root C:\mycode\Grammatical-Framework\gf-rgl `
  --output-root "$env:USERPROFILE\Downloads\Ars_Magna_Defluens\practical_single_previews"
```

Supported languages: `Eng Fre Spa Ger Dut Swe Dan Nor Nno Fin Est Afr Ita Por`.
Supported intentions: the 15 required scenario IDs from
`profiles/practical_generation_v1.json`.

The script emits a machine-readable JSON report containing `candidate`,
`archive_path`, `status`, `source_sha256`, `script_sha256`, and explicit flags:
`sa_semantic_request_executed=false`, `sa_bridge_verified=false`,
`released=false`, `linguistically_certified=false`. The WordBench archive
contains original stdout/stderr, the locked inputs, candidate and review form.

**Keep the two development lanes separate:** the five SA Konstellation cases
already exercise a real SA→GF candidate path; this 15-intent tool exercises the
original WordBench RGL probes but does *not* traverse SA.

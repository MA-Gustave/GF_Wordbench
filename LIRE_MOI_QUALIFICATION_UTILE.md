# GF WordBench — Interface de qualification utile

Depuis la fenêtre principale de GF WordBench, cliquer **Practical Qualification…**
(ou menu **Run → Practical Qualification…**). La fenêtre séparée se lance avec
Python 3.11+ et Tkinter. Alternative : double-cliquer sur
`Qualification_Langues_Utiles.pyw`.

L'application utilise le véritable module `gf_wordbench.practical.batch` :

- **Vérifier** : contrôle de conformité des pilotes, **sans GF**.
- **Smoke** : une seule sonde par langue, après vérification.
- **Full** : les **15 capacités obligatoires** de la documentation, après vérification.

Les **5 capacités facultatives sont exclues**. Les langues détectées dans la RGL mais sans pilote WordBench ne sont pas exécutées. Le catalogue fourni contient **20 langues préparées**. Les **14 langues retenues**
(`Eng Fre Spa Ger Dut Swe Dan Nor Nno Fin Est Afr Ita Por`) sont maintenant
présélectionnées par défaut. Les six autres restent disponibles via
**20 pilotes** pour les diagnostics. Aucun succès technique n'est une
certification linguistique.

Les résultats restent des **phrases candidates, non certifiées**. Aucun gold, RuntimeSet, ni publication n'est créé.

Documentation détaillée : `docs/practical/QUALIFICATION_UTILE_UI.md`.

### Installation avec l'archive prête pour C:\mycode

Depuis PowerShell :

```powershell
Expand-Archive `
  -LiteralPath "$env:USERPROFILE\Downloads\GF_Wordbench_Qualification_Utiles_UI_v1.0.zip" `
  -DestinationPath "C:\mycode\Grammatical-Framework" -Force

Start-Process -FilePath "C:\mycode\Grammatical-Framework\GF_Wordbench\Qualification_Langues_Utiles.pyw"
```

Les autres composants de WordBench ne sont pas remplacés par ce correctif.

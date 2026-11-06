# WordBench — v0.2.0, alignement lexical RGL des 14 langues

- Adaptation de 115 modules `.gf` sur 210 scénarios existants; 91 modules inchangés.
- Réutilisation `LexiconXXX` pour `book_N`, `house_N`, `say_VS`, `ready_A` selon la disponibilité réelle.
- Ajustements sélectifs d'accord, de lexèmes de retour et du passé événementiel.
- Recalcul des empreintes SHA-256 des sources GF et `.gfs`, conservation des 15 intentions.
- Module `alignment14.py` : vérification de provenance RGL, plan, application idempotente, vérification.
- Protection contre la régénération involontaire des sondes alignées.
- Lanceur Windows `Lancer_Alignement_14_Langues.bat` : `check`, `plan`, `apply`, `smoke`, `full`.
- Pas d'exécutable GF Windows disponible lors de la préparation. Pas de `.gold` nouvellement approuvé.
- Les six langues hors périmètre ne sont pas modifiées. RGL est en lecture seule.

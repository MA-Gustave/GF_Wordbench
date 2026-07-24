# ADR-0005 — Structured File and Scenario Results

| Champ | Valeur |
|---|---|
| Document role | Architectural decision record |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

## Contexte

Les consommateurs CLI, GUI, rapports et CI ont besoin des mêmes faits sans parser du texte humain.

## Décision

> **Les résultats fichier, compilation, scénario, gold et artefact sont représentés par des modèles structurés distincts.**

## Conséquences

Les rapports dérivent de ces modèles. Les états techniques, les statuts de validation, la causalité et les références de preuve restent séparés.

## Alternatives rejetées

Un résumé textuel unique masquerait des informations nécessaires à l’automatisation et à la traçabilité.

## Critères de vérification

- le contrat est couvert par des tests reproductibles ;
- la documentation propriétaire ne contredit pas cette décision ;
- `IMPLEMENTATION_ALIGNMENT.md` reflète l’état réel.

# ADR-0001 — Single Active Project

| Champ | Valeur |
|---|---|
| Document role | Architectural decision record |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

## Contexte

Les chemins, scénarios, golds, rapports et critères de release nécessitent une identité de projet non ambiguë.

## Décision

> **Un workspace GF Wordbench contient exactement un projet GF actif et chaque run normatif résout exactement une identité de projet.**

## Conséquences

Les faits projet appartiennent à `project/`. Un autre projet actif nécessite un autre workspace ou une opération explicite de remplacement. Les runs et l’état local restent isolés.

## Alternatives rejetées

Un registre de plusieurs projets actifs dans le même workspace ajouterait une seconde identité à chaque contrat et augmenterait le risque de dérive.

## Critères de vérification

- le contrat est couvert par des tests reproductibles ;
- la documentation propriétaire ne contredit pas cette décision ;
- `IMPLEMENTATION_ALIGNMENT.md` reflète l’état réel.

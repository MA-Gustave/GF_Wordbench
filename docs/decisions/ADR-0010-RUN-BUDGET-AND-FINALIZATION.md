# ADR-0010 — Run Budget and Finalization

| Champ | Valeur |
|---|---|
| Document role | Architectural decision record |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

## Contexte

Un run peut rencontrer timeout, annulation ou échec tardif tout en devant publier un état terminal vérifiable.

## Décision

> **Un run possède un budget global, des budgets d’étapes et une réserve de finalisation.**

## Conséquences

Le finalizer écrit atomiquement les résultats disponibles, arrête les enfants, distingue les états partiels et ne publie jamais une release `OK` incomplète.

## Alternatives rejetées

Des timeouts indépendants sans budget global peuvent consommer toute la durée et empêcher une finalisation fiable.

## Critères de vérification

- le contrat est couvert par des tests reproductibles ;
- la documentation propriétaire ne contredit pas cette décision ;
- `IMPLEMENTATION_ALIGNMENT.md` reflète l’état réel.

# ADR-0009 — GF Anti-Corruption Boundary

| Champ | Valeur |
|---|---|
| Document role | Architectural decision record |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

## Contexte

Les commandes, diagnostics et capacités GF varient selon les opérations et parfois les versions.

## Décision

> **Toutes les interactions GF passent par `GfToolPort` et une Anti-Corruption Layer dédiée.**

## Conséquences

L’ACL possède la construction des requêtes, les différences de version, l’interprétation des sorties, la vérification des `.gfo`/`.pgf` et les liens vers les preuves.

## Alternatives rejetées

Distribuer la syntaxe GF dans les stages, le domaine ou les interfaces créerait des contrats contradictoires.

## Critères de vérification

- le contrat est couvert par des tests reproductibles ;
- la documentation propriétaire ne contredit pas cette décision ;
- `IMPLEMENTATION_ALIGNMENT.md` reflète l’état réel.

# ADR-0011 — Separate Portfolio Product

| Champ | Valeur |
|---|---|
| Document role | Architectural decision record |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

## Contexte

La gestion de plusieurs workspaces introduit une identité et un cycle de vie distincts de la validation d’un projet actif.

## Décision

> **La gestion de plusieurs workspaces et les vues agrégées appartiennent à un produit compagnon indépendant.**

## Conséquences

Wordbench reste mono-projet. Le produit compagnon consomme uniquement des artefacts publics versionnés et ne devient jamais une dépendance d’exécution de Wordbench.

## Alternatives rejetées

Intégrer le portefeuille au cœur contredirait l’identité unique du workspace et élargirait inutilement les schémas, interfaces et responsabilités.

## Critères de vérification

- le contrat est couvert par des tests reproductibles ;
- la documentation propriétaire ne contredit pas cette décision ;
- `IMPLEMENTATION_ALIGNMENT.md` reflète l’état réel.

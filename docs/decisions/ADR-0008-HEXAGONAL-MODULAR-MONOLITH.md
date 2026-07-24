# ADR-0008 — Hexagonal Modular Monolith

| Champ | Valeur |
|---|---|
| Document role | Architectural decision record |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

## Contexte

Le produit possède plusieurs responsabilités stables, mais ne justifie pas une architecture distribuée.

## Décision

> **GF Wordbench utilise cinq modules fonctionnels et des frontières hexagonales dans un seul produit déployable.**

## Conséquences

Les APIs publiques intermodules sont étroites. Les ports représentent uniquement les frontières externes ou instables. Bootstrap assemble les implémentations.

## Alternatives rejetées

Des microservices, CQRS, Event Sourcing ou une interface par helper ajouteraient une complexité sans besoin démontré.

## Critères de vérification

- le contrat est couvert par des tests reproductibles ;
- la documentation propriétaire ne contredit pas cette décision ;
- `IMPLEMENTATION_ALIGNMENT.md` reflète l’état réel.

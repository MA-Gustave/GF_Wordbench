# ADR-0012 — Independent Products and Optional Interoperability

| Champ | Valeur |
|---|---|
| Document role | Architectural decision record |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

## Contexte

Plusieurs produits peuvent partager des concepts sans partager leur implémentation ou leur stockage privé.

## Décision

> **Toute interopérabilité avec un produit externe est optionnelle, versionnée et orientée consommateur.**

## Conséquences

Wordbench démarre et passe ses tests sans produit externe. Les exports publics appartiennent à Wordbench ; les adaptateurs spécifiques appartiennent de préférence au consommateur.

## Alternatives rejetées

Une base, un service obligatoire ou un package privé partagé empêcherait les déploiements indépendants.

## Critères de vérification

- le contrat est couvert par des tests reproductibles ;
- la documentation propriétaire ne contredit pas cette décision ;
- `IMPLEMENTATION_ALIGNMENT.md` reflète l’état réel.

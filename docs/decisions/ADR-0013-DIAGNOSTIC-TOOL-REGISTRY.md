# ADR-0013 — Diagnostic Tool Registry

| Champ | Valeur |
|---|---|
| Document role | Architectural decision record |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

## Contexte

Les diagnostics peuvent nécessiter plusieurs outils, certains mutables ou assistés par IA, avec des risques différents.

## Décision

> **Les outils diagnostiques exécutables sont enregistrés dans une allowlist statique avec contrats, limites et mutabilité déclarés.**

## Conséquences

Les flags, chemins, timeouts, tailles de sortie et rôles de preuve sont contrôlés. Les outils IA sont optionnels, visibles et non normatifs.

## Alternatives rejetées

L’exécution arbitraire de commandes ou plugins contournerait la frontière de processus et les contrôles de sécurité.

## Critères de vérification

- le contrat est couvert par des tests reproductibles ;
- la documentation propriétaire ne contredit pas cette décision ;
- `IMPLEMENTATION_ALIGNMENT.md` reflète l’état réel.

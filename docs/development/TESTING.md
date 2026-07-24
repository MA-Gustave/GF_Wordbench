# GF Wordbench — Testing

| Champ | Valeur |
|---|---|
| Document role | Test strategy |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

## Niveaux

- unit tests pour règles pures ;
- contract tests pour ports et APIs publiques ;
- schema tests pour formats persistés ;
- process tests avec faux exécutables ;
- integration tests avec GF réel ;
- end-to-end tests de la CLI ;
- parity tests CLI/GUI ;
- release tests fail-closed ;
- security tests de chemins et registre d’outils.

## Invariants à tester

- aucun appel processus hors adaptateur ;
- aucune commande GF hors ACL ;
- aucune release `OK` avec preuve manquante ;
- aucun rapport qui relance une étape ;
- aucun import privé intermodule ;
- aucune mutation de gold pendant `validate` ;
- exécution possible sans produit compagnon.

# GF Wordbench — Implementation Alignment

| Champ | Valeur |
|---|---|
| Document role | Implementation status ledger |
| Decision status | Accepted |
| Implementation status | Active tracking document |
| Verification status | Update with each implementation change |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

Ce document suit l’état réel sans modifier les décisions architecturales.

| Domaine | Décision | Implémentation | Vérification |
|---|---|---|---|
| Projet actif unique | Accepted | Documentation present | Code tests pending |
| Monolithe modulaire hexagonal | Accepted | Not implemented | Import tests pending |
| ACL GF | Accepted | Not implemented | Unit and real-GF tests pending |
| Process executor port/adapter | Accepted | Not implemented | Process tests pending |
| Validation quick | Accepted | Not implemented | End-to-end test pending |
| Scénarios et golds | Accepted | Documentation present | Execution tests pending |
| Reporting et manifeste | Accepted | Documentation present | Schema tests pending |
| Release gates | Accepted | Documentation present | Release test pending |
| Registre diagnostique | Accepted | Not implemented | Security tests pending |
| GUI partagée | Accepted | Not implemented | CLI/GUI parity tests pending |

## Règle de mise à jour

Un état passe à `Implemented` seulement lorsque le code existe. Il passe à `Verified` seulement lorsqu’un test reproductible couvre le contrat déclaré.

# GF Wordbench — Run Lifecycle

| Champ | Valeur |
|---|---|
| Document role | Run lifecycle authority |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

```text
CREATED → RESOLVED → RUNNING → FINALIZING → COMPLETED
                                  ├→ FAILED
                                  ├→ ERROR
                                  ├→ TIMED_OUT
                                  └→ CANCELLED
```

## Règles

- `run_id` est créé avant la première preuve ;
- la requête résolue est persistée ;
- les preuves sont écrites au fil de l’exécution ;
- une réserve de temps est conservée pour la finalisation ;
- les écritures finales sont atomiques ;
- un run terminal est immuable ;
- une reprise crée un nouveau run ou utilise une opération idempotente explicitement prévue.

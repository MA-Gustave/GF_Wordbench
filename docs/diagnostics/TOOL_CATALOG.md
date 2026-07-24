# GF Wordbench — Diagnostic Tool Catalog

| Champ | Valeur |
|---|---|
| Document role | Safe tool registry contract |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

Chaque outil enregistré déclare :

```text
tool_id
version
description
input_contract
allowed_flags
mutability
allowed_paths
timeout
output_limit
evidence_roles
ai_assisted
normative
```

## Politiques

- registre statique et reviewable ;
- aucun binaire ou flag arbitraire ;
- outils read-only par défaut ;
- opérations mutables séparées et confirmées ;
- IA optionnelle, visible et non normative ;
- sorties et versions enregistrées dans les preuves.

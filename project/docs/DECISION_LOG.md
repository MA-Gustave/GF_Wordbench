# Albanian (`Sqi`) — Decision Log

**Document role:** Project decision registry  
**Decision status:** Project-owned  
**Implementation status:** Decision summary reconciled with the supplied project configuration  
**Verification status:** Pending a current source inventory and reproducible GF Wordbench release run  
**Owner:** Albanian project maintainers  
**Last reviewed:** `2026-07-24`

## Accepted decisions

| ID | Decision |
|---|---|
| `PDEC-0001` | One active project per Wordbench workspace |
| `PDEC-0002` | `project/project.toml` owns active-project identity |
| `PDEC-0003` | Project identity is `sqi`; documented module family uses suffix `Sqi`; source directory is `lib/src/albanian` |
| `PDEC-0004` | GF remains the semantic execution authority |
| `PDEC-0005` | Static scanning is supplementary to GF validation |
| `PDEC-0006` | Public responsibilities have one provider |
| `PDEC-0007` | Dependencies follow the documented linguistic architecture |
| `PDEC-0008` | Structured lincats are not silently flattened |
| `PDEC-0009` | Checkpoints precede broad entrypoint validation |
| `PDEC-0010` | Project scenarios use native `.gfs` execution |
| `PDEC-0011` | Scenario output uses stable markers |
| `PDEC-0012` | Gold files are reviewed project assets |
| `PDEC-0013` | Normal validation never updates gold files |
| `PDEC-0014` | Raw evidence is preserved before interpretation |
| `PDEC-0015` | Normalization removes instability, not Albanian meaning |
| `PDEC-0016` | Incomplete states remain explicit |
| `PDEC-0017` | Required scenarios and open blockers govern release eligibility |
| `PDEC-0018` | Entrypoints and release artifacts are configured, not inferred |
| `PDEC-0019` | Historical diagnostics do not define current status |
| `PDEC-0024` | Required scenarios are `load`, `missing`, `linearize`, `parse`; optional scenarios are `generation`, `morphology` |

## Open decisions

| ID | Required decision |
|---|---|
| `PDEC-0020` | Primary Albanian variety |
| `PDEC-0021` | Canonical orthography and Unicode policy |
| `PDEC-0022` | Unique release/PGF entrypoint among configured entrypoints |
| `PDEC-0023` | Expected PGF filename and contents |
| `PDEC-0025` | Missing-function acceptance policy |
| `PDEC-0026` | Retirement path for extension scaffolding |
| `PDEC-0027` | Supported GF and RGL versions |
| `PDEC-0028` | Approved linguistic research authorities |

## Rejected approaches

| ID | Rejected approach |
|---|---|
| `PDEC-0029` | Use GUI state as active-project authority |
| `PDEC-0030` | Infer release roles from module filenames |
| `PDEC-0031` | Accept current scenario output automatically as gold |

## Record format

New decisions record date, status, context, decision, consequences, affected contracts and required evidence. Accepted records are immutable; a later record supersedes them explicitly.

"""Evaluate practical semantic coverage from a canonical Wordbench summary.

No language is accepted from source-file presence, compilability, or unreviewed
output alone. A passing golden comparison of each required scenario is needed.
This is a separate report, not a new general RGL release gate.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
PROFILE_ID = "gf-practical.profile"
RESULT_ID = "gf-practical.coverage-result"
RESULT_VERSION = "1.0"


def load_profile(path: Path) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    profile = json.loads(raw)
    if not isinstance(profile, dict) or profile.get("schema_id") != PROFILE_ID or profile.get("schema_version") != "1.0":
        raise ValueError("unsupported practical profile schema")
    if not isinstance(profile.get("profile_id"), str) or not profile["profile_id"]:
        raise ValueError("invalid profile ID")
    domains = profile.get("domains")
    capabilities = profile.get("capabilities")
    if not isinstance(domains, list) or not domains or len(set(domains)) != len(domains):
        raise ValueError("profile requires unique domains")
    if not all(isinstance(x, str) and IDENTIFIER.fullmatch(x) for x in domains):
        raise ValueError("invalid domain")
    if not isinstance(capabilities, list) or not capabilities:
        raise ValueError("profile requires capabilities")
    seen = set()
    for cap in capabilities:
        if not isinstance(cap, dict):
            raise ValueError("invalid capability")
        cid, scenarios, scopes = cap.get("id"), cap.get("scenario_ids"), cap.get("domains")
        if not isinstance(cid, str) or not IDENTIFIER.fullmatch(cid) or cid in seen:
            raise ValueError("invalid or duplicate capability ID")
        seen.add(cid)
        if type(cap.get("required")) is not bool:
            raise ValueError(f"capability {cid}: required must be boolean")
        if not isinstance(scopes, list) or not scopes or len(set(scopes)) != len(scopes) or not set(scopes).issubset(domains):
            raise ValueError(f"capability {cid}: invalid domains")
        if not isinstance(scenarios, list) or not scenarios or len(set(scenarios)) != len(scenarios) or not all(isinstance(s, str) and IDENTIFIER.fullmatch(s) for s in scenarios):
            raise ValueError(f"capability {cid}: scenario_ids must be unique GF Wordbench IDs")
    profile["profile_sha256"] = hashlib.sha256(raw).hexdigest()
    return profile


def selected_scenario_ids(profile: dict[str, Any], *, include_optional: bool = False) -> tuple[str, ...]:
    return tuple(dict.fromkeys(
        sid for cap in profile["capabilities"]
        if cap["required"] or include_optional
        for sid in cap["scenario_ids"]
    ))


def assess(profile: dict[str, Any], summary: dict[str, Any], *, language_key: str | None = None) -> dict[str, Any]:
    if summary.get("schema_id") != "gf-wordbench.run-summary" or summary.get("schema_version") != "1.0":
        raise ValueError("expected canonical GF Wordbench run-summary v1.0")
    metadata, totals, results = (summary.get("metadata"), summary.get("totals"), summary.get("scenario_results"))
    if not isinstance(metadata, dict) or not isinstance(totals, dict) or not isinstance(results, list):
        raise ValueError("malformed Wordbench summary")
    source_language = metadata.get("project_id")
    if not isinstance(source_language, str) or not source_language:
        raise ValueError("Wordbench summary lacks project identity")
    if language_key is not None and language_key != source_language:
        raise ValueError("language identity does not match Wordbench source summary")
    evidence = {}
    for item in results:
        if not isinstance(item, dict) or not isinstance(item.get("scenario_id"), str):
            raise ValueError("malformed scenario result")
        sid = item["scenario_id"]
        if sid in evidence:
            raise ValueError("duplicate scenario result")
        evidence[sid] = item
    run_ok = totals.get("overall_status") == "OK" and metadata.get("no_compile") is not True
    entries = []
    for cap in profile["capabilities"]:
        checks = []
        for sid in cap["scenario_ids"]:
            item = evidence.get(sid)
            if item is None:
                state, reason = "unverified", "scenario_absent"
            elif item.get("status") in ("FAIL", "ERROR"):
                state, reason = "failed", "scenario_failed"
            elif item.get("status") != "OK":
                state, reason = "unverified", "scenario_not_executed"
            elif item.get("timed_out") is True or item.get("exit_code") != 0:
                state, reason = "failed", "process_not_successful"
            elif item.get("gold_match") is not True or not item.get("gold_path"):
                state, reason = "unverified", "reviewed_gold_not_proven"
            elif item.get("normalized_output_path") is None:
                state, reason = "unverified", "normalized_output_missing"
            elif any(not sec.get("completed", False) for sec in item.get("sections", []) if isinstance(sec, dict)):
                state, reason = "failed", "scenario_section_incomplete"
            else:
                state, reason = "passed", "reviewed_gold_passed"
            checks.append({"scenario_id": sid, "status": state, "reason": reason})
        states = {check["status"] for check in checks}
        state = "failed" if "failed" in states else ("passed" if states == {"passed"} else "unverified")
        if state == "passed" and not run_ok:
            state = "unverified"
            checks.append({"scenario_id": None, "status": "unverified", "reason": "overall_run_not_verified"})
        entries.append({"id": cap["id"], "domains": cap["domains"], "required": cap["required"], "status": state, "checks": checks})
    domains = []
    for domain in profile["domains"]:
        required = [entry for entry in entries if domain in entry["domains"] and entry["required"]]
        passed = sum(entry["status"] == "passed" for entry in required)
        failures = [entry["id"] for entry in required if entry["status"] == "failed"]
        unknown = [entry["id"] for entry in required if entry["status"] == "unverified"]
        state = "ready" if passed == len(required) and run_ok else ("needs_work" if failures else "unverified")
        domains.append({"domain": domain, "status": state, "required_total": len(required), "required_passed": passed, "coverage_ratio": round(passed / len(required), 4) if required else 0.0, "missing": failures, "unverified": unknown})
    overall = "ready" if all(d["status"] == "ready" for d in domains) else ("needs_work" if any(d["status"] == "needs_work" for d in domains) else "unverified")
    return {"schema_id": RESULT_ID, "schema_version": RESULT_VERSION,
            "profile_id": profile["profile_id"], "profile_version": profile["profile_version"], "profile_sha256": profile["profile_sha256"],
            "language_key": source_language, "wordbench_run_id": metadata.get("run_id"), "wordbench_run_status": totals.get("overall_status"),
            "status": overall, "domains": domains, "capabilities": entries,
            "evidence_type": "gf-wordbench.run-summary", "evidence_note": "Source artifact only; integrity must be separately verified by Observatory."}


def write_result(result: dict[str, Any], path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Result file is separate from the immutable Wordbench run; never modify summary/manifest.
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)

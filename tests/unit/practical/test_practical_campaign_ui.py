"""Tests for the GUI's safety boundaries (no Tk mainloop or GF required)."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import queue
import sys
import threading
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
GUI = ROOT / "Qualification_Langues_Utiles.pyw"
loader = importlib.machinery.SourceFileLoader("practical_ui_under_test", str(GUI))
spec = importlib.util.spec_from_loader(loader.name, loader)
ui = importlib.util.module_from_spec(spec)
loader.exec_module(ui)


class TestPracticalCampaignUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.languages, cls.required = ui.catalog_and_scope(ROOT)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tmpdir = Path(self.tmp.name)
        self.gf = self.tmpdir / "compiler" / "gf.exe"
        self.gf.parent.mkdir()
        self.gf.write_bytes(b"not the real GF binary; argument construction only")
        self.rgl = self.tmpdir / "rgl"
        for c in self.languages:
            (self.rgl / "src" / c["rgl"]).mkdir(parents=True, exist_ok=True)
        (self.rgl / "src" / "api").mkdir(exist_ok=True)
        self.output = self.tmpdir / "output"

    def _minimal_repo(self) -> Path:
        dest = self.tmpdir / "clone"
        for relative in ("profiles/practical_generation_v1.json",
                         "pilots/practical_generation_v1/language_catalog.json",
                         "src/gf_wordbench/practical/batch.py"):
            f = dest / relative
            f.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, f)
        for c in self.languages:
            relative = f"pilots/practical_generation_v1/{c['code']}/pilot_manifest.json"
            f = dest / relative
            f.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, f)
        return dest

    def test_20_languages_and_15_required_are_derived_from_repo(self):
        self.assertEqual(20, len(self.languages))
        self.assertEqual(tuple(ui.APPROVED_REQUIRED), self.required)
        self.assertTrue(all(x["manifest_issue"] is None for x in self.languages))

    def test_focus_14_is_default_and_matches_review_subset(self):
        self.assertEqual(14, len(ui.FOCUS14))
        self.assertEqual(14, len(ui.preferred_14_languages(self.languages)))
        self.assertEqual(list(ui.FOCUS14), ui.preferred_14_languages(self.languages))
        from gf_wordbench.practical.review14 import FOCUS14 as review_focus
        self.assertEqual(tuple(review_focus), ui.FOCUS14)
        self.assertEqual({'Sqi', 'Cze', 'Pol', 'Rus', 'Hrv', 'Gre'},
                         {entry['code'] for entry in self.languages} - set(ui.FOCUS14))

    def test_focus_does_not_auto_expand_when_one_language_missing(self):
        truncated = [item for item in self.languages if item['code'] != 'Fre']
        self.assertEqual(13, len(ui.preferred_14_languages(truncated)))
        self.assertNotIn('Fre', ui.preferred_14_languages(truncated))
        incomplete = [dict(item, manifest_issue='mismatch') if item['code'] == 'Ger'
                      else item for item in truncated]
        self.assertEqual(12, len(ui.preferred_14_languages(incomplete)))
        self.assertNotIn('Ger', ui.preferred_14_languages(incomplete))

    def test_optional_capabilities_never_get_included(self):
        self.assertEqual(5, len(ui.APPROVED_OPTIONAL))
        self.assertTrue(set(self.required).isdisjoint(ui.APPROVED_OPTIONAL))
        self.assertNotIn("counterfactual", self.required)
        self.assertNotIn("habitual", self.required)

    def test_check_needs_no_compiler_or_rgl(self):
        check, run = ui.build_commands(ROOT, ["Fre", "Eng"], "check",
                          self.tmpdir / "absent-gf", self.tmpdir / "absent-rgl",
                          self.tmpdir / "nowhere", 90, 600, python="python")
        self.assertIsNone(run)
        self.assertEqual(["python", "-u", "-m", "gf_wordbench.practical.batch", "check",
                          "--languages", "Fre", "Eng"], check)

    def test_full_uses_exact_cli_without_optional_flags(self):
        check, run = ui.build_commands(ROOT, ["Eng", "Fre"], "full", self.gf, self.rgl,
                                         self.output, 90, 600, python="python")
        self.assertEqual("check", check[4])
        self.assertEqual("run", run[4])
        self.assertEqual("full", run[run.index("--mode")+1])
        self.assertEqual("600", run[run.index("--max-minutes")+1])
        self.assertEqual(["Eng", "Fre"], run[run.index("--languages")+1:])
        self.assertNotIn("--scenario", run)
        self.assertNotIn("--practical-profile", run)

    def test_smoke_uses_smoke_mode(self):
        _, run = ui.build_commands(ROOT, ["Eng"], "smoke", self.gf, self.rgl,
                                   self.output, 100, 50, python="python")
        self.assertEqual("smoke", run[run.index("--mode")+1])

    def test_duplicate_or_unknown_language_refused(self):
        for selected in (["Eng", "Eng"], ["Xxx"], []):
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                ui.build_commands(ROOT, selected, "full", self.gf, self.rgl,
                                  self.output, 90, 600)

    def test_changed_required_scope_refused(self):
        clone = self._minimal_repo()
        p = clone / "profiles" / "practical_generation_v1.json"
        profile = json.loads(p.read_text(encoding="utf-8"))
        cap = next(c for c in profile["capabilities"] if c["id"] == "counterfactual")
        cap["required"] = True
        p.write_text(json.dumps(profile), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Profil modifié"):
            ui.catalog_and_scope(clone)

    def test_extra_unapproved_scenario_refused(self):
        clone = self._minimal_repo()
        path = clone / "pilots/practical_generation_v1/Eng/pilot_manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["scenarios"].append({"id": "counterfactual"})
        path.write_text(json.dumps(manifest), encoding="utf-8")
        entries, _ = ui.catalog_and_scope(clone)
        self.assertIsNotNone(entries[0]["manifest_issue"])
        with self.assertRaisesRegex(ValueError, "non préparé"):
            ui.build_commands(clone, ["Eng"], "full", self.gf, self.rgl,
                              self.output, 90, 600)

    def test_missing_rgl_language_is_explicit(self):
        (self.rgl / "src" / "french").rmdir()
        with self.assertRaisesRegex(ValueError, "RGL absente"):
            ui.build_commands(ROOT, ["Fre"], "full", self.gf, self.rgl,
                              self.output, 90, 600)

    def test_output_never_inside_sources_or_ancestors(self):
        for folder in (ROOT / "results", self.rgl / "out", self.gf.parent / "out",
                       ROOT.parent):
            with self.subTest(folder=str(folder)), self.assertRaises(ValueError):
                ui.validate_output_root(folder, ROOT, self.rgl, self.gf)
        ui.validate_output_root(self.output, ROOT, self.rgl, self.gf)

    def test_invalid_limits_refused(self):
        for timeout, budget in ((0, 600), (90, 0), (3601, 600), (90, 1441)):
            with self.subTest(limits=(timeout,budget)), self.assertRaises(ValueError):
                ui.build_commands(ROOT, ["Eng"], "full", self.gf, self.rgl,
                                  self.output, timeout, budget)

    def test_rgl_detected_but_not_prepared_is_informational(self):
        api = self.rgl / "src" / "api"
        (api / "SyntaxEng.gf").write_text("", encoding="utf-8")
        (api / "SyntaxJpn.gf").write_text("", encoding="utf-8")
        codes = ui.detected_rgl_codes(self.rgl, {x["code"] for x in self.languages})
        self.assertEqual(["Jpn"], codes)

    def test_summary_must_not_claim_certification(self):
        report = {"status":"completed_unverified", "languages_requested":["Eng"],
                  "totals":{"languages_attempted":1,"languages_unattempted":0,
                            "candidate_for_review":15,"probe_failed":0,"timeout":0,
                            "languages_with_issues":0}}
        v, summary = ui.summarize_campaign(report, ["Eng"])
        self.assertIn("NON CERTIFIÉS", v)
        self.assertIn("15 candidats", summary)
        report["totals"]["languages_unattempted"] = 1
        v, _ = ui.summarize_campaign(report, ["Eng"])
        self.assertIn("PARTIEL", v)

    def test_partial_run_is_detected_without_archive(self):
        d = self.output / "defluens-batch-full-20261105-A"
        d.mkdir(parents=True)
        data = {"schema_id":"defluens.pilot-batch", "status":"running", "totals":{},
                "languages_requested":["Eng"]}
        (d / "batch_summary.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual((None,None), ui.load_summary_from_new_run(self.output, "full", {d.name}))
        found, parsed = ui.load_summary_from_new_run(self.output, "full", set())
        self.assertEqual(d, found)
        self.assertEqual("running", parsed["status"])

    def _fake_background(self, preflight_ok: bool):
        program = self.tmpdir / "fake_process.py"
        program.write_text("""
import json, sys
from pathlib import Path
mode = sys.argv[1]
if mode == 'check':
    print(json.dumps({'schema_id': 'defluens.batch-preflight', 'ok': %s,
      'languages': [{'language':'Eng', 'status':'preflight_ok' if %s else 'preflight_failed'}]}))
else:
    root = Path(sys.argv[2])
    p = root / 'defluens-batch-full-test'
    p.mkdir(parents=True)
    summary = {'schema_id':'defluens.pilot-batch','status':'completed_unverified',
      'languages_requested':['Eng'],
      'entries':[{'language':'Eng','status':'candidate_for_review'}],
      'totals':{'languages_attempted':1,'languages_unattempted':0,
                'candidate_for_review':15,'languages_with_issues':0},
      'archive_path': str(root/'defluens-batch-full-test.zip')}
    (p/'batch_summary.json').write_text(json.dumps(summary),encoding='utf-8')
    (root/'defluens-batch-full-test.zip').write_bytes(b'synthetic test only')
""" % ("True" if preflight_ok else "False", "True" if preflight_ok else "False"), encoding="utf-8")
        class Headless:
            _run_process = ui.QualificationWindow._run_process
            _background = ui.QualificationWindow._background
            _terminate_process_tree = ui.QualificationWindow._terminate_process_tree
            def __init__(self):
                self.process = None
                self.events = queue.Queue()
                self.stop_event = threading.Event()
        launcher = Headless()
        check = [sys.executable, str(program), 'check']
        run = [sys.executable, str(program), 'run', str(self.output)]
        launcher._background(ROOT, self.output, ['Eng'], 'full', check, run)
        results = []
        while not launcher.events.empty():
            results.append(launcher.events.get_nowait())
        return results

    def test_background_run_verdict_is_candidate_only(self):
        events = self._fake_background(preflight_ok=True)
        done = next(item for kind,item in events if kind == 'finished')
        self.assertIn('NON CERTIFIÉS', done[0])
        self.assertEqual('completed_unverified', done[2]['status'])
        self.assertTrue((self.output / 'defluens-batch-full-test.zip').is_file())

    def test_preflight_failure_never_invokes_gf_step(self):
        events = self._fake_background(preflight_ok=False)
        done = next(item for kind,item in events if kind == 'finished')
        self.assertIn('BLOCAGE', done[0])
        self.assertFalse((self.output / 'defluens-batch-full-test').exists())


if __name__ == "__main__":
    unittest.main()

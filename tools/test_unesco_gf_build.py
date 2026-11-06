from pathlib import Path
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'tools'))
import unesco_gf_build as build

class WordbenchCandidateTests(unittest.TestCase):
    def test_missing_gf_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)
            (p/'UnescoPilot.gf').write_text('abstract UnescoPilot = {}',encoding='utf-8')
            (p/'UnescoPilotFre.gf').write_text('concrete UnescoPilotFre of UnescoPilot = {}',encoding='utf-8')
            result=build.compile_candidate(p,'fr',p/'missing.exe',5)
            self.assertEqual(result['status'],'BLOCKED')
            self.assertFalse(result['pgf_compiled'])
            self.assertFalse(result['release_authorized'])
            self.assertTrue((p/'wordbench-build.json').is_file())

    def test_reject_malformed_language(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):
                build.compile_candidate(Path(t),'de',Path('gf.exe'))


    def test_wordbench_native_process_without_artifact_is_blocked(self):
        # A deliberately fake process cannot prove that a grammar was built.
        import os
        if os.name == 'nt':
            self.skipTest('Unix-only stub executable')
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);tool=p/'gf'
            tool.write_text('#!/bin/sh\nexit 0\n',encoding='utf-8');tool.chmod(0o755)
            (p/'UnescoPilot.gf').write_text('abstract UnescoPilot = {}',encoding='utf-8')
            (p/'UnescoPilotFre.gf').write_text('concrete UnescoPilotFre of UnescoPilot = {}',encoding='utf-8')
            result=build.compile_candidate(p,'fr',tool,6)
            self.assertEqual(result['status'],'BLOCKED_COMPILATION_OR_ARTIFACT')
            self.assertFalse(result['pgf_compiled'])
            self.assertFalse(result['release_authorized'])

if __name__=='__main__':unittest.main()

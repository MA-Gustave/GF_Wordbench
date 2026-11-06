"""Tests for launching the separate practical window without Qt/GF startup."""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gf_wordbench.entrypoints.gui import practical_tool


class PracticalToolLaunchTests(unittest.TestCase):
    def test_default_root_and_tool_are_real_repository_members(self):
        root = practical_tool.wordbench_root()
        script = practical_tool.qualifier_script()
        self.assertEqual(root / 'Qualification_Langues_Utiles.pyw', script)
        self.assertTrue((root / 'src/gf_wordbench/practical/batch.py').is_file())

    def test_missing_tool_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(FileNotFoundError, 'not installed'):
                practical_tool.qualifier_script(Path(td))

    def test_missing_batch_module_fails_closed_even_with_pyw(self):
        with tempfile.TemporaryDirectory() as td:
            script = Path(td) / 'Qualification_Langues_Utiles.pyw'
            script.write_text('# sample')
            with self.assertRaisesRegex(FileNotFoundError, 'not installed'):
                practical_tool.qualifier_script(Path(td))

    def test_executable_is_python_not_installed_gui_entrypoint(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            scripts = root / '.venv' / ('Scripts' if os.name == 'nt' else 'bin')
            scripts.mkdir(parents=True)
            tool = scripts / ('pythonw.exe' if os.name == 'nt' else 'python3')
            tool.write_bytes(b'test stub')
            bogus = scripts / ('gf-wordbench-gui.exe' if os.name == 'nt' else 'gf-wordbench-gui')
            bogus.write_bytes(b'not python')
            chosen = practical_tool.python_for_qualifier(root, running_python=str(bogus))
            self.assertEqual(str(tool), chosen)

    def test_detached_launch_never_runs_gf_and_preserves_working_dir(self):
        import sys
        import types
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            script = root / 'Qualification_Langues_Utiles.pyw'
            script.write_text('# stub')
            module = root / 'src/gf_wordbench/practical/batch.py'
            module.parent.mkdir(parents=True)
            module.write_text('# stub')
            seen = []
            class FakeQProcess:
                @staticmethod
                def startDetached(executable, args, cwd):
                    seen.append((executable, args, cwd))
                    return True, 4321
            qt_module = types.ModuleType('PySide6.QtCore')
            qt_module.QProcess = FakeQProcess
            base = types.ModuleType('PySide6')
            base.QtCore = qt_module
            with patch.dict(sys.modules, {'PySide6': base, 'PySide6.QtCore': qt_module}):
                self.assertEqual(4321, practical_tool.launch_qualification(root))
            self.assertEqual(1, len(seen))
            self.assertEqual([str(script)], seen[0][1])
            self.assertEqual(str(root), seen[0][2])
            self.assertIn('python', Path(seen[0][0]).name.lower())

    def test_failed_detached_start_is_reported(self):
        import sys
        import types
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'Qualification_Langues_Utiles.pyw').write_text('# stub')
            module = root / 'src/gf_wordbench/practical/batch.py'
            module.parent.mkdir(parents=True)
            module.write_text('# stub')
            class FakeQProcess:
                @staticmethod
                def startDetached(executable, args, cwd):
                    return False, 0
            qt_module = types.ModuleType('PySide6.QtCore')
            qt_module.QProcess = FakeQProcess
            base = types.ModuleType('PySide6')
            base.QtCore = qt_module
            with patch.dict(sys.modules, {'PySide6': base, 'PySide6.QtCore': qt_module}):
                with self.assertRaisesRegex(OSError, 'Could not start'):
                    practical_tool.launch_qualification(root)

    def test_running_python_can_be_used_for_detached_tool(self):
        import sys
        selected = practical_tool.python_for_qualifier(running_python=sys.executable)
        self.assertTrue(Path(selected).is_file())


if __name__ == '__main__':
    unittest.main()

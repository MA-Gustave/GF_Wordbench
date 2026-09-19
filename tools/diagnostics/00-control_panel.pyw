"""Control panel for the GF Wordbench mini diagnostic suite."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import threading
import time

from diag_core import console_python, detect_repo_root, load_config, open_path

LEVELS = (
    (
        "N01",
        "Environment",
        "01-environment.pyw",
        "Installation, paths, tools, and imports",
    ),
    (
        "N02",
        "Repository Integrity",
        "02-repository_integrity.pyw",
        "Static repository and tooling checks",
    ),
    (
        "N03",
        "Contracts",
        "03-contracts.pyw",
        "CLI, schema, and architecture contract tests",
    ),
    (
        "N04",
        "Runtime Smoke",
        "04-runtime_smoke.pyw",
        "Public CLI and optional quick-run smoke",
    ),
    (
        "N05",
        "Release Validation",
        "08-release_validation.pyw",
        "Run and inspect Wordbench release evidence",
    ),
    (
        "N06",
        "GUI Startup Lifecycle",
        "06-gui_startup_lifecycle.pyw",
        "Canonical GUI startup API and lifecycle checks",
    ),
    (
        "N07",
        "Multilanguage Switching",
        "07-multilanguage_switching.pyw",
        "Language switching and cross-language isolation",
    ),
)


class ControlPanel:
    def __init__(self) -> None:
        import tkinter as tk
        from tkinter import messagebox, ttk

        self.tk = tk
        self.ttk = ttk
        self.messagebox = messagebox
        self.root = tk.Tk()
        self.config = load_config()
        self.suite_root = Path(__file__).resolve().parent
        self.root.title("GF Wordbench Mini Diagnostics")
        self.root.geometry("980x650")
        self.root.minsize(800, 520)
        self.status = tk.StringVar(value="Ready")
        self._build()
        self.log(f"Repository: {self.config.repo_root}")
        self.log(
            f"Language path: {self.config.language_path or 'not configured'}"
        )
        self.log(
            "Validation profile: "
            f"{self.config.validation_profile or 'not configured'}"
        )

    def _build(self) -> None:
        outer = self.ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)
        self.ttk.Label(
            outer,
            text="GF Wordbench Mini Diagnostics",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")
        self.ttk.Label(
            outer,
            text=(
                "Thin diagnostic launchers over Wordbench's CLI, tests, and existing "
                "validation scripts. The suite does not replace Wordbench validation."
            ),
            wraplength=920,
        ).pack(anchor="w", pady=(2, 10))

        table_frame = self.ttk.Frame(outer)
        table_frame.pack(fill="both", expand=True)
        self.tree = self.ttk.Treeview(
            table_frame,
            columns=("name", "purpose"),
            show="tree headings",
            selectmode="browse",
        )
        self.tree.heading("#0", text="Level")
        self.tree.heading("name", text="Name")
        self.tree.heading("purpose", text="Purpose")
        self.tree.column("#0", width=70, stretch=False)
        self.tree.column("name", width=190, stretch=False)
        self.tree.column("purpose", width=600)
        self.tree.pack(side="left", fill="both", expand=True)

        scroll = self.ttk.Scrollbar(table_frame, command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)

        for level_id, name, filename, purpose in LEVELS:
            self.tree.insert(
                "",
                "end",
                iid=filename,
                text=level_id,
                values=(name, purpose),
            )

        self.tree.selection_set(LEVELS[0][2])

        buttons = self.ttk.Frame(outer)
        buttons.pack(fill="x", pady=8)
        self.ttk.Button(
            buttons,
            text="Open selected",
            command=self.open_selected,
        ).pack(side="left")
        self.ttk.Button(
            buttons,
            text="Run selected headless",
            command=self.run_selected_headless,
        ).pack(side="left", padx=6)
        self.ttk.Button(
            buttons,
            text="Run safe suite N01–N04",
            command=self.run_safe_suite,
        ).pack(side="left", padx=6)
        self.ttk.Button(
            buttons,
            text="Open artifacts",
            command=lambda: open_path(self.config.artifact_root),
        ).pack(side="left", padx=6)
        self.ttk.Button(
            buttons,
            text="Open repository",
            command=lambda: open_path(self.config.repo_root),
        ).pack(side="left", padx=6)
        self.ttk.Label(
            buttons,
            textvariable=self.status,
        ).pack(side="right")

        log_frame = self.ttk.LabelFrame(outer, text="Launcher log")
        log_frame.pack(fill="both", expand=True)
        self.log_text = self.tk.Text(
            log_frame,
            height=10,
            wrap="word",
            font=("Consolas", 9),
        )
        self.log_text.pack(fill="both", expand=True)

    def log(self, message: str) -> None:
        self.log_text.insert(
            "end",
            f"[{time.strftime('%H:%M:%S')}] {message}\n",
        )
        self.log_text.see("end")

    def selected_script(self) -> Path | None:
        selection = self.tree.selection()
        if not selection:
            return None
        return self.suite_root / selection[0]

    def open_selected(self) -> None:
        script = self.selected_script()
        if script is None:
            return

        command = [sys.executable, str(script)]
        if sys.platform.startswith("win"):
            pythonw = Path(sys.executable).with_name("pythonw.exe")
            if pythonw.is_file():
                command[0] = str(pythonw)

        subprocess.Popen(
            command,
            cwd=str(self.config.repo_root),
        )
        self.log(f"Launched {script.name}")

    def run_selected_headless(self) -> None:
        script = self.selected_script()
        if script is None:
            return

        self._run_background(
            [console_python(), str(script), "--headless"],
            script.name,
        )

    def run_safe_suite(self) -> None:
        runner = self.suite_root / "run_safe_suite.py"
        self._run_background(
            [console_python(), str(runner)],
            "safe suite",
        )

    def _run_background(self, command: list[str], label: str) -> None:
        self.status.set("RUNNING")

        def worker() -> None:
            completed = subprocess.run(
                command,
                cwd=str(self.config.repo_root),
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            output = completed.stdout or ""

            def finish() -> None:
                self.log(f"{label} exited with {completed.returncode}")
                if output:
                    self.log(output[-6000:])
                self.status.set(
                    "PASS" if completed.returncode == 0 else "FAIL"
                )

            self.root.after(0, finish)

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()

    def mainloop(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    ControlPanel().mainloop()
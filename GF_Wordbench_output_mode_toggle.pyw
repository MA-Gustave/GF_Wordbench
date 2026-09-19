from __future__ import annotations

import datetime as _dt
import os
import re
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

APP_TITLE = "GF Wordbench — Mode de sortie GF"
RELATIVE_TARGET = (
    Path("GF_Wordbench") / "GF_Wordbench" / "src" / "gf_wordbench"
    / "validation" / "compilation" / "gf_adapter.py"
)

START_MARKER = "    if isinstance(payload, ModuleCompilePayload):"
END_MARKER = '        metadata["target_module"] = payload.module_name'

VERBOSE_BEGIN = "        # GF_WORDBENCH_VERBOSE_DIAG_BEGIN"
VERBOSE_END = "        # GF_WORDBENCH_VERBOSE_DIAG_END"

VERBOSE_BLOCK = """\
        # GF_WORDBENCH_VERBOSE_DIAG_BEGIN
        # Diagnostic only: ask GF to print per-function PMCFG progress.
        command = GfCommand(
            operation=command.operation,
            executable=command.executable,
            arguments=("-v", *command.arguments),
            working_directory=command.working_directory,
            gf_search_paths=command.gf_search_paths,
            profile_id=command.profile_id,
        )
        # GF_WORDBENCH_VERBOSE_DIAG_END"""


def _candidate_roots() -> list[Path]:
    here = Path(__file__).resolve().parent
    roots: list[Path] = []

    def add(p: Path) -> None:
        try:
            p = p.resolve()
        except OSError:
            return
        if p not in roots:
            roots.append(p)

    add(here)
    add(here.parent)
    add(Path(r"C:\mycode\Grammatical_Framework"))

    for parent in here.parents:
        add(parent)
        if parent.name.lower() == "grammatical_framework":
            break

    return roots


def _find_target() -> Path:
    for root in _candidate_roots():
        target = root / RELATIVE_TARGET
        if target.is_file():
            return target

    suffix = (
        Path("src") / "gf_wordbench" / "validation"
        / "compilation" / "gf_adapter.py"
    )
    for root in _candidate_roots():
        target = root / suffix
        if target.is_file():
            return target

    raise FileNotFoundError(
        "Impossible de trouver gf_adapter.py.\n\n"
        "Place ce .pyw dans C:\\mycode\\Grammatical_Framework "
        "ou conserve l'arborescence Wordbench habituelle."
    )


def _decode_source(path: Path) -> tuple[str, bool]:
    raw = path.read_bytes()
    had_bom = raw.startswith(b"\xef\xbb\xbf")
    return raw.decode("utf-8-sig"), had_bom


def _encode_source(text: str, had_bom: bool) -> bytes:
    raw = text.encode("utf-8")
    return (b"\xef\xbb\xbf" + raw) if had_bom else raw


def _span(text: str) -> tuple[int, int]:
    start = text.find(START_MARKER)
    if start < 0:
        raise RuntimeError("Bloc ModuleCompilePayload introuvable dans gf_adapter.py.")
    end = text.find(END_MARKER, start)
    if end < 0:
        raise RuntimeError("Fin du bloc ModuleCompilePayload introuvable.")
    return start, end


def _block(text: str) -> str:
    start, end = _span(text)
    return text[start:end]


def _state(text: str) -> str:
    block = _block(text)

    if VERBOSE_BEGIN in block or VERBOSE_END in block:
        if VERBOSE_BEGIN not in block or VERBOSE_END not in block:
            raise RuntimeError("Bloc diagnostic VERBOSE incomplet.")
        return "verbose"

    if re.search(r"(?m)^\s*quiet\s*=\s*False\s*,\s*$", block):
        return "warnings"

    return "quiet"


def _remove_verbose(block: str) -> str:
    pattern = (
        r"(?ms)\r?\n^[ \t]*# GF_WORDBENCH_VERBOSE_DIAG_BEGIN[ \t]*\r?\n"
        r".*?"
        r"^[ \t]*# GF_WORDBENCH_VERBOSE_DIAG_END[ \t]*"
    )
    new_block, count = re.subn(pattern, "", block, count=1)
    if count != 1:
        raise RuntimeError("Impossible de retirer proprement le bloc VERBOSE.")
    return new_block


def _ensure_quiet_false(block: str) -> str:
    if re.search(r"(?m)^\s*quiet\s*=\s*False\s*,\s*$", block):
        return block

    new_block, count = re.subn(
        r"(?m)^([ \t]*)quiet\s*=\s*True\s*,[ \t]*$",
        r"\1quiet=False,",
        block,
        count=1,
    )
    if count == 1:
        return new_block

    pattern = (
        r"(?m)^([ \t]*)output_dir\s*=\s*payload\.output_directory\s*,"
        r"[ \t]*(\r?\n)"
    )
    match = re.search(pattern, block)
    if not match:
        raise RuntimeError(
            "Point d'insertion output_dir=payload.output_directory introuvable."
        )
    indent = match.group(1)
    newline = match.group(2)
    insertion = match.group(0) + f"{indent}quiet=False,{newline}"
    return block[:match.start()] + insertion + block[match.end():]


def _remove_quiet_override(block: str) -> str:
    block, _ = re.subn(
        r"(?m)^[ \t]*quiet\s*=\s*False\s*,[ \t]*(?:\r?\n)",
        "",
        block,
        count=1,
    )
    block, _ = re.subn(
        r"(?m)^[ \t]*quiet\s*=\s*True\s*,[ \t]*(?:\r?\n)",
        "",
        block,
        count=1,
    )
    return block


def _insert_verbose(block: str) -> str:
    if VERBOSE_BEGIN in block:
        return block

    close_candidates = list(re.finditer(r"(?m)^        \)[ \t]*$", block))
    if not close_candidates:
        raise RuntimeError("Fin de build_module_compile_command introuvable.")

    match = close_candidates[-1]
    newline = "\r\n" if "\r\n" in block else "\n"
    insert_at = match.end()
    verbose = VERBOSE_BLOCK.replace("\n", newline)
    return block[:insert_at] + newline + verbose + block[insert_at:]


def _cycle(text: str) -> tuple[str, str]:
    start, end = _span(text)
    block = text[start:end]
    state = _state(text)

    if state == "quiet":
        new_block = _ensure_quiet_false(block)
        new_state = "warnings"
    elif state == "warnings":
        new_block = _ensure_quiet_false(block)
        new_block = _insert_verbose(new_block)
        new_state = "verbose"
    else:
        new_block = _remove_verbose(block)
        new_block = _remove_quiet_override(new_block)
        new_state = "quiet"

    return text[:start] + new_block + text[end:], new_state


def _backup(path: Path) -> Path:
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(f"{path.name}.output-mode-toggle.{stamp}.bak")
    counter = 1
    while backup.exists():
        backup = path.with_name(
            f"{path.name}.output-mode-toggle.{stamp}_{counter}.bak"
        )
        counter += 1
    shutil.copy2(path, backup)
    return backup


def _atomic_write(path: Path, data: bytes) -> None:
    temp = path.with_name(path.name + ".output-mode-toggle.tmp")
    temp.write_bytes(data)
    os.replace(temp, path)


def _state_text(state: str) -> tuple[str, str]:
    if state == "quiet":
        return "SILENCIEUX", "GF reçoit -s. Prochain clic : afficher les warnings."
    if state == "warnings":
        return "WARNINGS", "quiet=False, sans -s. Prochain clic : activer GF -v."
    return "VERBOSE", "quiet=False + GF -v. Prochain clic : retour au mode silencieux."


class ToggleApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title(APP_TITLE)
        root.resizable(False, False)
        self.target: Path | None = None

        frame = tk.Frame(root, padx=18, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="GF Wordbench — niveau de sortie du compilateur",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")

        self.state_label = tk.Label(
            frame, text="Détection…", font=("Segoe UI", 10, "bold"), pady=10
        )
        self.state_label.pack(anchor="w")

        self.detail_label = tk.Label(
            frame, text="", font=("Segoe UI", 9), justify="left", wraplength=720
        )
        self.detail_label.pack(anchor="w")

        self.path_label = tk.Label(
            frame, text="", font=("Segoe UI", 8), justify="left", wraplength=720
        )
        self.path_label.pack(anchor="w", pady=(8, 12))

        self.button = tk.Button(
            frame, text="Basculer vers le mode suivant", width=34, command=self.toggle
        )
        self.button.pack(anchor="w")

        tk.Label(
            frame,
            text=(
                "Après chaque bascule, ferme complètement Wordbench puis relance-le "
                "avant Run Validation."
            ),
            font=("Segoe UI", 9),
            pady=12,
        ).pack(anchor="w")

        self.refresh()

    def refresh(self) -> None:
        try:
            self.target = _find_target()
            text, _ = _decode_source(self.target)
            state = _state(text)
            title, detail = _state_text(state)
            self.state_label.config(text=f"État : {title}")
            self.detail_label.config(text=detail)
            self.path_label.config(text=str(self.target))
            self.button.config(state="normal")
        except Exception as exc:
            self.target = None
            self.state_label.config(text="État : ERREUR")
            self.detail_label.config(text=str(exc))
            self.path_label.config(text="")
            self.button.config(state="disabled")

    def toggle(self) -> None:
        if self.target is None:
            return
        try:
            text, had_bom = _decode_source(self.target)
            old_state = _state(text)
            new_text, new_state = _cycle(text)

            if new_text == text:
                raise RuntimeError("Aucune modification produite.")

            backup = _backup(self.target)
            _atomic_write(self.target, _encode_source(new_text, had_bom))

            verify_text, _ = _decode_source(self.target)
            verified_state = _state(verify_text)
            if verified_state != new_state:
                raise RuntimeError(
                    f"Vérification après écriture échouée : {verified_state}."
                )

            old_title, _ = _state_text(old_state)
            new_title, new_detail = _state_text(new_state)

            messagebox.showinfo(
                APP_TITLE,
                "Bascule réussie.\n\n"
                f"{old_title}  →  {new_title}\n"
                f"{new_detail}\n\n"
                f"Sauvegarde :\n{backup}\n\n"
                "Relance Wordbench avant le prochain test.",
            )
            self.refresh()

        except Exception as exc:
            messagebox.showerror(
                APP_TITLE,
                "Aucune modification sûre n'a été appliquée.\n\n" + str(exc),
            )
            self.refresh()


def main() -> None:
    root = tk.Tk()
    ToggleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

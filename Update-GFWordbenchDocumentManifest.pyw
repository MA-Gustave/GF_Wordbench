# -*- coding: utf-8 -*-
"""
GF Wordbench — Mise à jour de DOCUMENT_MANIFEST.json

Application graphique Windows sans dépendance externe.

Principes :
- analyse en lecture seule par défaut ;
- conserve la liste et l'ordre des entrées existantes ;
- recalcule size et sha256 à partir des octets actuels ;
- ne liste jamais DOCUMENT_MANIFEST.json lui-même ;
- détecte les chemins manquants, absolus, dupliqués ou hors dépôt ;
- peut retirer les entrées manquantes seulement sur option explicite ;
- sauvegarde l'ancien manifeste hors du dépôt ;
- écrit en UTF-8 sans BOM, LF, JSON indenté, avec newline finale ;
- vérifie toutes les entrées après écriture.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import shutil
import sys
import tempfile
import traceback
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


SCRIPT_VERSION = "1.0.0-document-manifest-updater"
DEFAULT_REPOSITORY = Path(__file__).resolve().parent
MANIFEST_NAME = "DOCUMENT_MANIFEST.json"


@dataclass(frozen=True)
class EntryState:
    path: str
    exists: bool
    old_size: int | None
    new_size: int | None
    old_sha256: str | None
    new_sha256: str | None

    @property
    def changed(self) -> bool:
        return (
            self.exists
            and (
                self.old_size != self.new_size
                or (self.old_sha256 or "").lower()
                != (self.new_sha256 or "").lower()
            )
        )


@dataclass
class AnalysisResult:
    repository: Path
    manifest_path: Path
    source_manifest: dict
    entries: list[EntryState]
    invalid_paths: list[str]
    duplicate_paths: list[str]

    @property
    def missing(self) -> list[EntryState]:
        return [entry for entry in self.entries if not entry.exists]

    @property
    def changed(self) -> list[EntryState]:
        return [entry for entry in self.entries if entry.changed]


def normalize_repository(text: str) -> Path:
    path = Path(text.strip().strip('"')).expanduser()
    return path.resolve(strict=False)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def validate_relative_path(path_text: str) -> bool:
    if not isinstance(path_text, str) or not path_text.strip():
        return False

    if "\\" in path_text:
        return False

    path = PurePosixPath(path_text)

    if path.is_absolute():
        return False

    if any(part in ("", ".", "..") for part in path.parts):
        return False

    if ":" in path_text:
        return False

    if path.as_posix().casefold() == MANIFEST_NAME.casefold():
        return False

    return True


def safe_join(repository: Path, manifest_path: str) -> Path:
    candidate = repository.joinpath(*PurePosixPath(manifest_path).parts)
    resolved_candidate = candidate.resolve(strict=False)
    resolved_repository = repository.resolve(strict=False)

    try:
        resolved_candidate.relative_to(resolved_repository)
    except ValueError as exc:
        raise ValueError(
            f"Chemin hors dépôt : {manifest_path}"
        ) from exc

    return resolved_candidate


def load_manifest(manifest_path: Path) -> dict:
    raw = manifest_path.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        text = raw[3:].decode("utf-8", errors="strict")
    else:
        text = raw.decode("utf-8", errors="strict")

    data = json.loads(text)

    if not isinstance(data, dict):
        raise ValueError("Le manifeste doit être un objet JSON.")

    if "files" not in data or not isinstance(data["files"], list):
        raise ValueError(
            "Le manifeste doit contenir un tableau JSON nommé 'files'."
        )

    for index, entry in enumerate(data["files"]):
        if not isinstance(entry, dict):
            raise ValueError(
                f"L'entrée files[{index}] n'est pas un objet JSON."
            )
        if "path" not in entry:
            raise ValueError(
                f"L'entrée files[{index}] ne contient pas 'path'."
            )

    return data


def analyze_manifest(repository: Path) -> AnalysisResult:
    if not repository.is_dir():
        raise FileNotFoundError(f"Dépôt introuvable : {repository}")

    manifest_path = repository / MANIFEST_NAME
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"Manifeste introuvable : {manifest_path}"
        )

    source_manifest = load_manifest(manifest_path)

    invalid_paths: list[str] = []
    duplicate_paths: list[str] = []
    entries: list[EntryState] = []
    seen: set[str] = set()

    for entry in source_manifest["files"]:
        path_text = entry.get("path")

        if not validate_relative_path(path_text):
            invalid_paths.append(str(path_text))
            continue

        normalized_key = path_text.casefold()
        if normalized_key in seen:
            duplicate_paths.append(path_text)
            continue
        seen.add(normalized_key)

        full_path = safe_join(repository, path_text)
        exists = full_path.is_file()

        if exists:
            new_size = full_path.stat().st_size
            new_sha256 = sha256_file(full_path)
        else:
            new_size = None
            new_sha256 = None

        old_size_value = entry.get("size")
        old_size = (
            int(old_size_value)
            if isinstance(old_size_value, int)
            and not isinstance(old_size_value, bool)
            else None
        )

        old_hash_value = entry.get("sha256")
        old_sha256 = (
            old_hash_value
            if isinstance(old_hash_value, str)
            else None
        )

        entries.append(
            EntryState(
                path=path_text,
                exists=exists,
                old_size=old_size,
                new_size=new_size,
                old_sha256=old_sha256,
                new_sha256=new_sha256,
            )
        )

    return AnalysisResult(
        repository=repository,
        manifest_path=manifest_path,
        source_manifest=source_manifest,
        entries=entries,
        invalid_paths=invalid_paths,
        duplicate_paths=duplicate_paths,
    )


def backup_manifest(manifest_path: Path) -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        backup_base = Path(local_app_data)
    else:
        backup_base = Path(tempfile.gettempdir())

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_directory = (
        backup_base
        / "GF_Wordbench"
        / "document-manifest-backups"
        / timestamp
    )
    backup_directory.mkdir(parents=True, exist_ok=False)

    backup_path = backup_directory / MANIFEST_NAME
    shutil.copy2(manifest_path, backup_path)
    return backup_path


def build_updated_manifest(
    analysis: AnalysisResult,
    *,
    remove_missing: bool,
) -> dict:
    current_by_path = {
        entry.path.casefold(): entry
        for entry in analysis.entries
    }

    updated_files: list[dict] = []

    for source_entry in analysis.source_manifest["files"]:
        path_text = source_entry.get("path")

        if not validate_relative_path(path_text):
            raise ValueError(
                f"Chemin invalide dans le manifeste : {path_text}"
            )

        state = current_by_path.get(path_text.casefold())
        if state is None:
            raise ValueError(
                f"Entrée non analysable ou dupliquée : {path_text}"
            )

        if not state.exists:
            if remove_missing:
                continue
            raise FileNotFoundError(
                "Fichier référencé mais absent : "
                f"{path_text}"
            )

        updated_entry = dict(source_entry)
        updated_entry["path"] = path_text
        updated_entry["sha256"] = state.new_sha256
        updated_entry["size"] = state.new_size
        updated_files.append(updated_entry)

    updated_manifest = dict(analysis.source_manifest)
    updated_manifest["generated_at"] = dt.date.today().isoformat()
    updated_manifest["files"] = updated_files
    return updated_manifest


def serialize_manifest(manifest: dict) -> bytes:
    text = json.dumps(
        manifest,
        ensure_ascii=False,
        indent=2,
    )
    return (text + "\n").encode("utf-8")


def atomic_write(path: Path, content: bytes) -> None:
    temporary_path: Path | None = None

    try:
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
        )
        temporary_path = Path(temporary_name)

        with os.fdopen(file_descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temporary_path, path)
        temporary_path = None

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def verify_manifest(repository: Path) -> tuple[int, list[str]]:
    analysis = analyze_manifest(repository)

    errors: list[str] = []

    if analysis.invalid_paths:
        errors.extend(
            f"Chemin invalide : {path}"
            for path in analysis.invalid_paths
        )

    if analysis.duplicate_paths:
        errors.extend(
            f"Chemin dupliqué : {path}"
            for path in analysis.duplicate_paths
        )

    for entry in analysis.entries:
        if not entry.exists:
            errors.append(f"Fichier absent : {entry.path}")
        elif entry.changed:
            errors.append(
                f"Intégrité incorrecte : {entry.path}"
            )

    return len(analysis.entries), errors


class ManifestUpdaterApplication(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("GF Wordbench — DOCUMENT_MANIFEST updater")
        self.geometry("1040x720")
        self.minsize(850, 560)

        self.repository_var = tk.StringVar(
            value=str(DEFAULT_REPOSITORY)
        )
        self.remove_missing_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(
            value="Prêt. Lancez l'analyse en lecture seule."
        )
        self.last_analysis: AnalysisResult | None = None

        self._build_interface()

    def _build_interface(self) -> None:
        main = ttk.Frame(self, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        repository_frame = ttk.LabelFrame(
            main,
            text="Dépôt",
            padding=10,
        )
        repository_frame.pack(fill=tk.X)

        ttk.Entry(
            repository_frame,
            textvariable=self.repository_var,
        ).pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            padx=(0, 8),
        )

        ttk.Button(
            repository_frame,
            text="Parcourir…",
            command=self.choose_repository,
        ).pack(side=tk.LEFT)

        options = ttk.Frame(main, padding=(0, 10, 0, 8))
        options.pack(fill=tk.X)

        ttk.Checkbutton(
            options,
            text=(
                "Retirer du manifeste les entrées dont "
                "le fichier est absent"
            ),
            variable=self.remove_missing_var,
            command=self.refresh_apply_state,
        ).pack(side=tk.LEFT)

        ttk.Label(
            options,
            text=f"Version : {SCRIPT_VERSION}",
        ).pack(side=tk.RIGHT)

        buttons = ttk.Frame(main)
        buttons.pack(fill=tk.X, pady=(0, 8))

        self.analyze_button = ttk.Button(
            buttons,
            text="Analyser — dry-run",
            command=self.analyze,
        )
        self.analyze_button.pack(side=tk.LEFT)

        self.apply_button = ttk.Button(
            buttons,
            text="Mettre à jour le manifeste",
            command=self.apply_update,
            state=tk.DISABLED,
        )
        self.apply_button.pack(side=tk.LEFT, padx=(8, 0))

        ttk.Button(
            buttons,
            text="Effacer le journal",
            command=self.clear_log,
        ).pack(side=tk.RIGHT)

        ttk.Label(
            main,
            textvariable=self.status_var,
        ).pack(fill=tk.X, pady=(0, 6))

        log_frame = ttk.LabelFrame(
            main,
            text="Journal",
            padding=6,
        )
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log = tk.Text(
            log_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            state=tk.DISABLED,
        )
        self.log.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
        )

        vertical = ttk.Scrollbar(
            log_frame,
            orient=tk.VERTICAL,
            command=self.log.yview,
        )
        vertical.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.configure(yscrollcommand=vertical.set)

        horizontal = ttk.Scrollbar(
            main,
            orient=tk.HORIZONTAL,
            command=self.log.xview,
        )
        horizontal.pack(fill=tk.X)
        self.log.configure(xscrollcommand=horizontal.set)

    def choose_repository(self) -> None:
        selected = filedialog.askdirectory(
            title="Sélectionner le dépôt GF Wordbench",
            initialdir=self.repository_var.get(),
        )
        if selected:
            self.repository_var.set(selected)
            self.last_analysis = None
            self.apply_button.configure(state=tk.DISABLED)

    def clear_log(self) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)

    def append_log(self, message: str = "") -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)
        self.update_idletasks()

    def set_busy(self, busy: bool) -> None:
        self.analyze_button.configure(
            state=tk.DISABLED if busy else tk.NORMAL
        )
        if busy:
            self.apply_button.configure(state=tk.DISABLED)
            self.configure(cursor="watch")
        else:
            self.configure(cursor="")

    def refresh_apply_state(self) -> None:
        analysis = self.last_analysis
        allowed = (
            analysis is not None
            and not analysis.invalid_paths
            and not analysis.duplicate_paths
            and (
                not analysis.missing
                or self.remove_missing_var.get()
            )
        )
        self.apply_button.configure(
            state=tk.NORMAL if allowed else tk.DISABLED
        )

    def analyze(self) -> None:
        self.set_busy(True)
        self.clear_log()
        self.status_var.set("Analyse du manifeste…")

        try:
            repository = normalize_repository(
                self.repository_var.get()
            )
            analysis = analyze_manifest(repository)
            self.last_analysis = analysis

            self.append_log(
                f"Version                      : {SCRIPT_VERSION}"
            )
            self.append_log("Mode                         : DRY-RUN")
            self.append_log(
                f"Dépôt                        : {repository}"
            )
            self.append_log(
                f"Manifeste                    : "
                f"{analysis.manifest_path}"
            )
            self.append_log(
                f"Entrées analysées            : "
                f"{len(analysis.entries)}"
            )
            self.append_log(
                f"Entrées à actualiser         : "
                f"{len(analysis.changed)}"
            )
            self.append_log(
                f"Fichiers manquants           : "
                f"{len(analysis.missing)}"
            )
            self.append_log(
                f"Chemins invalides            : "
                f"{len(analysis.invalid_paths)}"
            )
            self.append_log(
                f"Chemins dupliqués            : "
                f"{len(analysis.duplicate_paths)}"
            )
            self.append_log("")

            for entry in analysis.changed:
                self.append_log(
                    f"[UPDATE] {entry.path}"
                )
                self.append_log(
                    f"    size   : {entry.old_size} -> "
                    f"{entry.new_size}"
                )
                self.append_log(
                    f"    sha256 : {entry.old_sha256} -> "
                    f"{entry.new_sha256}"
                )

            if analysis.missing:
                self.append_log("")
                self.append_log("Fichiers manquants :")
                for entry in analysis.missing:
                    self.append_log(f"  - {entry.path}")

            if analysis.invalid_paths:
                self.append_log("")
                self.append_log("Chemins invalides :")
                for path in analysis.invalid_paths:
                    self.append_log(f"  - {path}")

            if analysis.duplicate_paths:
                self.append_log("")
                self.append_log("Chemins dupliqués :")
                for path in analysis.duplicate_paths:
                    self.append_log(f"  - {path}")

            self.append_log("")
            self.append_log("Aucune modification effectuée.")

            if analysis.missing:
                self.status_var.set(
                    "Analyse terminée : des fichiers manquent. "
                    "Restaurez-les ou cochez leur retrait explicite."
                )
            else:
                self.status_var.set(
                    f"Analyse terminée : "
                    f"{len(analysis.changed)} entrée(s) à actualiser."
                )

        except Exception as exc:
            self.last_analysis = None
            self.status_var.set("Échec de l'analyse.")
            self.append_log("ERREUR")
            self.append_log(str(exc))
            self.append_log("")
            self.append_log(traceback.format_exc())
            messagebox.showerror(
                "Erreur d'analyse",
                str(exc),
                parent=self,
            )

        finally:
            self.set_busy(False)
            self.refresh_apply_state()

    def apply_update(self) -> None:
        analysis = self.last_analysis
        if analysis is None:
            messagebox.showinfo(
                "Analyse requise",
                "Lancez d'abord l'analyse.",
                parent=self,
            )
            return

        remove_missing = self.remove_missing_var.get()

        if analysis.missing and not remove_missing:
            messagebox.showerror(
                "Fichiers manquants",
                (
                    "Des fichiers du manifeste sont absents. "
                    "Restaurez-les ou cochez l'option de retrait."
                ),
                parent=self,
            )
            return

        removed_count = len(analysis.missing) if remove_missing else 0
        confirmation = messagebox.askyesno(
            "Confirmer la mise à jour",
            (
                f"Actualiser {len(analysis.changed)} entrée(s)"
                + (
                    f" et retirer {removed_count} entrée(s) manquante(s)"
                    if removed_count
                    else ""
                )
                + " ?\n\n"
                "L'ancien manifeste sera sauvegardé hors du dépôt."
            ),
            parent=self,
        )
        if not confirmation:
            return

        self.set_busy(True)
        self.status_var.set("Mise à jour du manifeste…")
        self.append_log("")
        self.append_log("=== APPLICATION ===")

        backup_path: Path | None = None

        try:
            # Recalculer immédiatement avant écriture.
            fresh = analyze_manifest(
                normalize_repository(self.repository_var.get())
            )

            if fresh.invalid_paths:
                raise ValueError(
                    "Le manifeste contient des chemins invalides."
                )
            if fresh.duplicate_paths:
                raise ValueError(
                    "Le manifeste contient des chemins dupliqués."
                )
            if fresh.missing and not remove_missing:
                raise FileNotFoundError(
                    "Des fichiers du manifeste sont absents."
                )

            updated = build_updated_manifest(
                fresh,
                remove_missing=remove_missing,
            )

            backup_path = backup_manifest(fresh.manifest_path)
            atomic_write(
                fresh.manifest_path,
                serialize_manifest(updated),
            )

            entry_count, verification_errors = verify_manifest(
                fresh.repository
            )
            if verification_errors:
                shutil.copy2(backup_path, fresh.manifest_path)
                details = "\n".join(
                    f"- {error}"
                    for error in verification_errors[:25]
                )
                raise RuntimeError(
                    "Vérification échouée. "
                    "Le manifeste précédent a été restauré.\n"
                    f"{details}"
                )

            self.last_analysis = None
            self.apply_button.configure(state=tk.DISABLED)

            self.append_log(
                f"Manifeste mis à jour         : "
                f"{fresh.manifest_path}"
            )
            self.append_log(
                f"Entrées finales              : {entry_count}"
            )
            self.append_log(
                f"Entrées retirées             : {removed_count}"
            )
            self.append_log(
                f"Sauvegarde                   : {backup_path}"
            )
            self.append_log(
                "Vérification                 : OK"
            )

            self.status_var.set(
                "Manifeste mis à jour et vérifié."
            )

            messagebox.showinfo(
                "Mise à jour terminée",
                (
                    f"Le manifeste contient {entry_count} entrée(s).\n"
                    "Tous les chemins, tailles et SHA-256 sont valides.\n\n"
                    f"Sauvegarde :\n{backup_path}"
                ),
                parent=self,
            )

        except Exception as exc:
            self.status_var.set("Échec de la mise à jour.")
            self.append_log("ERREUR")
            self.append_log(str(exc))
            self.append_log("")
            self.append_log(traceback.format_exc())

            messagebox.showerror(
                "Échec de la mise à jour",
                str(exc),
                parent=self,
            )

        finally:
            self.set_busy(False)
            self.refresh_apply_state()


def main() -> None:
    application = ManifestUpdaterApplication()
    application.mainloop()


if __name__ == "__main__":
    main()

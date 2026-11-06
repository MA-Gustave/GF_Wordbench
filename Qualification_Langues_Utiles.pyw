# -*- coding: utf-8 -*-
"""GF WordBench practical pilot launcher (Windows, Python 3.11+, Tkinter).

A UI on top of the existing gf_wordbench.practical.batch CLI. Never edits RGL,
never rewrites scenario manifests and never labels candidates as certified.
"""
from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import queue
import re
import signal
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_VERSION = "1.1"
# Exact bounded subset used by WordBench practical.review14.FOCUS14.
# A default selection is NOT a linguistic certification.
FOCUS14 = ("Eng", "Fre", "Spa", "Ger", "Dut", "Swe", "Dan",
           "Nor", "Nno", "Fin", "Est", "Afr", "Ita", "Por")
APPROVED_REQUIRED = (
    "factual-present", "past-event", "past-state", "future-reference", "factual-negation",
    "temporal-order", "condition-real", "possibility", "source-attribution", "quantity",
    "location", "instruction", "prohibition", "obligation", "conditional-instruction",
)
APPROVED_OPTIONAL = (
    "anteriority", "process-ongoing", "passive-or-rephrase", "counterfactual", "habitual",
)
LANGUAGE_NAMES = {
    "Eng": "English", "Fre": "Français", "Sqi": "Shqip", "Spa": "Español",
    "Ger": "Deutsch", "Dut": "Nederlands", "Swe": "Svenska", "Dan": "Dansk",
    "Nor": "Norsk", "Nno": "Nynorsk", "Fin": "Suomi", "Est": "Eesti",
    "Cze": "Čeština", "Pol": "Polski", "Rus": "Русский", "Hrv": "Hrvatski",
    "Gre": "Ελληνικά", "Afr": "Afrikaans", "Ita": "Italiano", "Por": "Português",
}
PROGRESS_RE = re.compile(r"^\[(\d+)/(\d+)\]\s+([A-Za-z]{3})\s+[—-]")
SCENARIO_RE = re.compile(r"^\s+\((\d+)/(\d+)\)\s+(\S+):\s+(\w+)")
BG = "#F3F6FA"
NAVY = "#162C42"
ACCENT = "#116F75"
SLATE = "#52657A"


def repository_layout(wordbench: Path) -> tuple[Path, Path, Path]:
    repo = Path(wordbench).expanduser().resolve()
    return (repo / "pilots" / "practical_generation_v1" / "language_catalog.json",
            repo / "profiles" / "practical_generation_v1.json",
            repo / "src" / "gf_wordbench" / "practical" / "batch.py")


def catalog_and_scope(wordbench: Path) -> tuple[list[dict], tuple[str, ...]]:
    """Fail closed on any drift from the agreed 15 required + 5 optional profile."""
    catalog_path, profile_path, batch_path = repository_layout(wordbench)
    if not batch_path.is_file():
        raise ValueError("Module de campagne WordBench absent : " + str(batch_path))
    for path in (catalog_path, profile_path):
        if not path.is_file():
            raise ValueError("Fichier WordBench absent : " + str(path))
    catalog = json.loads(catalog_path.read_text(encoding="utf-8-sig"))
    profile = json.loads(profile_path.read_text(encoding="utf-8-sig"))
    entries = profile.get("capabilities")
    if not isinstance(entries, list):
        raise ValueError("Profil pratique sans liste capabilities")
    ids_required = [c["id"] for c in entries if c.get("required") is True]
    ids_optional = [c["id"] for c in entries if c.get("required") is False]
    if (ids_required != list(APPROVED_REQUIRED) or
            set(ids_optional) != set(APPROVED_OPTIONAL) or len(entries) != 20 or
            len({c["id"] for c in entries}) != 20):
        raise ValueError("Profil modifié : les 15 capacités utiles et les 5 facultatives "
                         "ne correspondent plus au périmètre accepté. Exécution bloquée.")
    langs = catalog.get("languages")
    campaign = catalog.get("default_campaign")
    if not isinstance(langs, dict) or not isinstance(campaign, list) or not campaign:
        raise ValueError("Catalogue des langues WordBench invalide")
    if len(campaign) != len(set(campaign)):
        raise ValueError("Langues dupliquées dans la campagne")
    result = []
    pilots_root = catalog_path.parent
    for code in campaign:
        entry = langs.get(code)
        if not isinstance(code, str) or not re.fullmatch(r"[A-Za-z]{3}", code) or not isinstance(entry, dict):
            raise ValueError(f"Langue non prise en charge par le catalogue : {code!r}")
        rgl_dir = entry.get("rgl_directory")
        if not isinstance(rgl_dir, str) or not re.fullmatch(r"[a-z][a-z0-9_-]+", rgl_dir):
            raise ValueError(f"Répertoire RGL invalide pour {code}")
        manifest_path = pilots_root / code / "pilot_manifest.json"
        manifest_issue = None
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            found = [x.get("id") for x in manifest["scenarios"]]
            if (manifest.get("language_code") != code or
                    manifest.get("rgl_directory") != rgl_dir or found != list(APPROVED_REQUIRED)):
                raise ValueError("identités ou 15 scénarios non conformes")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            manifest_issue = str(exc)[:250]
        result.append({"code": code, "name": LANGUAGE_NAMES.get(code, code), "rgl": rgl_dir,
                       "manifest_issue": manifest_issue})
    return result, tuple(APPROVED_REQUIRED)


def preferred_14_languages(available: list[dict]) -> list[str]:
    """Only select prepared, conforming members of the bounded 14-language focus.

    An absent or incomplete language is never silently replaced by a different
    language merely to reach fourteen.
    """
    eligible = {entry["code"] for entry in available if not entry["manifest_issue"]}
    return [code for code in FOCUS14 if code in eligible]


def detected_rgl_codes(rgl: Path, prepared: set[str]) -> list[str]:
    """Informational inventory only: never run non-prepared RGL languages."""
    api_dir = Path(rgl) / "src" / "api"
    if not api_dir.is_dir():
        return []
    codes = {p.stem[6:] for p in api_dir.glob("Syntax???.gf") if p.is_file()}
    return sorted(c for c in codes if c not in prepared)


def validate_output_root(output: Path, wordbench: Path, rgl: Path, gf: Path) -> None:
    """Match WordBench's protections and reject outputs in repositories or toolchains."""
    resolved = Path(output).expanduser().resolve()
    if resolved == Path(resolved.anchor):
        raise ValueError("Le dossier de résultats doit être un sous-dossier dédié.")
    for source in (Path(wordbench), Path(rgl), Path(gf).parent):
        src = source.expanduser().resolve()
        if resolved == src or resolved.is_relative_to(src) or src.is_relative_to(resolved):
            raise ValueError("Les résultats doivent rester en dehors des sources et de leurs parents : " + str(src))


def build_commands(wordbench: Path, codes: list[str], mode: str, gf: Path, rgl: Path,
                   output: Path, timeout: int, budget: int, python: str | None = None) -> tuple[list[str], list[str] | None]:
    if mode not in ("check", "smoke", "full") or not codes or len(set(codes)) != len(codes):
        raise ValueError("Mode ou sélection de langues invalide")
    available, required = catalog_and_scope(wordbench)
    known = {x["code"] for x in available if not x["manifest_issue"]}
    if not set(codes).issubset(known):
        raise ValueError("Sélection contient un profil non préparé ou incomplet")
    if len(required) != 15:
        raise ValueError("Le profil n'a pas 15 capacités obligatoires")
    py = python or python_executable()
    base = [py, "-u", "-m", "gf_wordbench.practical.batch"]
    check = base + ["check", "--languages", *codes]
    if mode == "check":
        return check, None
    if not 1 <= timeout <= 3600 or not 1 <= budget <= 1440:
        raise ValueError("Timeout autorisé : 1-3600 s ; durée globale : 1-1440 min")
    if not Path(gf).is_file():
        raise ValueError("gf.exe introuvable : " + str(gf))
    if not (Path(rgl) / "src").is_dir():
        raise ValueError("Sources RGL introuvables : " + str(rgl))
    for item in available:
        if item["code"] in codes and not (Path(rgl) / "src" / item["rgl"]).is_dir():
            raise ValueError(f"RGL absente pour {item['code']} : {item['rgl']}")
    validate_output_root(output, wordbench, rgl, gf)
    run = base + ["run", "--mode", mode, "--gf-executable", str(gf),
                  "--rgl-root", str(rgl), "--output-root", str(output),
                  "--timeout", str(timeout), "--max-minutes", str(budget),
                  "--languages", *codes]
    return check, run


def python_executable() -> str:
    current = Path(sys.executable)
    if current.name.lower() == "pythonw.exe":
        sibling = current.with_name("python.exe")
        if sibling.is_file():
            return str(sibling)
    return str(current)


def summarize_campaign(report: dict, selected: list[str]) -> tuple[str, str]:
    totals = report.get("totals") or {}
    attempted = int(totals.get("languages_attempted", 0))
    unattempted = int(totals.get("languages_unattempted", max(0, len(selected)-attempted)))
    errors = int(totals.get("probe_failed", 0))
    timeouts = int(totals.get("timeout", 0))
    candidates = int(totals.get("candidate_for_review", 0))
    unexpected = report.get("languages_requested") != selected
    state = report.get("status", "inconnu")
    if unexpected or unattempted or state != "completed_unverified":
        verdict = "PARTIEL / À REPRENDRE"
    elif errors or timeouts or int(totals.get("languages_with_issues", 0)):
        verdict = "TERMINÉ AVEC ANOMALIES"
    else:
        verdict = "TERMINÉ — CANDIDATS NON CERTIFIÉS"
    detail = (f"{state}  ·  {attempted}/{len(selected)} langues tentées  ·  "
              f"{candidates} candidats  ·  {errors} erreurs  ·  {timeouts} délais  ·  "
              f"{unattempted} langues non tentées")
    return verdict, detail


def load_summary_from_new_run(output: Path, mode: str, before: set[str]) -> tuple[Path | None, dict | None]:
    root = Path(output)
    if not root.is_dir():
        return None, None
    dirs = [p for p in root.glob(f"defluens-batch-{mode}-*")
            if p.is_dir() and p.name not in before and (p / "batch_summary.json").is_file()]
    for directory in sorted(dirs, key=lambda p: p.stat().st_mtime_ns, reverse=True):
        try:
            data = json.loads((directory / "batch_summary.json").read_text(encoding="utf-8"))
            if data.get("schema_id") == "defluens.pilot-batch":
                return directory, data
        except (OSError, ValueError):
            pass
    return None, None


class QualificationWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("GF WordBench — Qualification utile (14 langues recommandées)")
        self.root.geometry("1210x835")
        self.root.minsize(980, 760)
        self.events: queue.Queue = queue.Queue()
        self.worker: threading.Thread | None = None
        self.process: subprocess.Popen | None = None
        self.stop_event = threading.Event()
        self.exit_after_cancel = False
        self.codes: list[str] = []
        self.items: dict[str, dict] = {}
        self.row_status: dict[str, str] = {}
        self.last_zip: Path | None = None
        self.last_dir: Path | None = None
        self.active_mode: str | None = None
        self.selected_codes: list[str] = []
        base = Path(__file__).resolve().parent
        if not (base / "src" / "gf_wordbench").is_dir():
            base = Path(r"C:\mycode\Grammatical-Framework\GF_Wordbench\GF_Wordbench")
        framework = (
            base.parent.parent
            if base.name.casefold() == "gf_wordbench"
            and base.parent.name.casefold() == "gf_wordbench"
            else base.parent
        )
        self.wordbench = tk.StringVar(value=str(base))
        self.gf = tk.StringVar(value=str(framework / "gf-3.12-windows" / "gf.exe"))
        self.rgl = tk.StringVar(value=str(framework / "gf-rgl"))
        self.output = tk.StringVar(value=str(Path.home() / "Downloads" / "Ars_Magna_Defluens" / "practical_pilot_runs"))
        self.timeout = tk.StringVar(value="90")
        self.budget = tk.StringVar(value="600")
        self.overview = tk.StringVar(value="Charge les profils pratiques WordBench pour commencer.")
        self.status = tk.StringVar(value="Prêt")
        self.progress_msg = tk.StringVar(value="Aucune opération en cours")
        self.progress_count = tk.DoubleVar(value=0)
        self._configure_style()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.refresh_catalog()
        self.root.after(100, self._poll)

    def _configure_style(self) -> None:
        st = ttk.Style(self.root)
        if "clam" in st.theme_names():
            st.theme_use("clam")
        st.configure("TFrame", background=BG)
        st.configure("TLabel", background=BG, foreground=NAVY, font=("Segoe UI", 10))
        st.configure("TButton", font=("Segoe UI", 10), padding=(8, 4))
        st.configure("Accent.TButton", background=ACCENT, foreground="white", borderwidth=0)
        st.map("Accent.TButton", background=[("active", "#155F65"), ("disabled", "#BCC8D2")])
        st.configure("TLabelframe", background=BG, bordercolor="#D5DEE8")
        st.configure("TLabelframe.Label", background=BG, foreground=NAVY, font=("Segoe UI", 10, "bold"))
        st.configure("Treeview", font=("Segoe UI", 10), rowheight=27, background="white", fieldbackground="white", foreground=NAVY)
        st.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), padding=(6, 7))
        st.configure("Horizontal.TProgressbar", background=ACCENT, troughcolor="#DDE5ED")

    def _build_ui(self) -> None:
        page = ttk.Frame(self.root, padding=17)
        page.pack(fill="both", expand=True)
        header = tk.Frame(page, bg=NAVY, padx=17, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="GF WordBench  /  Qualification utile", bg=NAVY, fg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(header, text="14 langues retenues par défaut · 15 capacités utiles · 5 facultatives exclues · candidats non certifiés",
                 bg=NAVY, fg="#D7E6EC", font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))
        tabs = ttk.Notebook(page)
        tabs.pack(fill="both", expand=True, pady=(9, 2))
        main_tab = ttk.Frame(tabs, padding=(2, 3))
        logs_tab = ttk.Frame(tabs, padding=11)
        tabs.add(main_tab, text="   Campagne & langues   ")
        tabs.add(logs_tab, text="   Journal & verdict   ")
        self.tabs = tabs
        settings = ttk.LabelFrame(main_tab, text=" Chemins et limites ", padding=7)
        settings.pack(fill="x", pady=(12, 8))
        settings.columnconfigure(1, weight=1)
        for r, (text, var, kind) in enumerate([
            ("WordBench", self.wordbench, "directory"), ("GF 3.12", self.gf, "file"),
            ("RGL", self.rgl, "directory"), ("Résultats", self.output, "directory")]):
            ttk.Label(settings, text=text, width=12).grid(row=r, column=0, sticky="w", pady=3)
            ttk.Entry(settings, textvariable=var).grid(row=r, column=1, sticky="ew", padx=(4, 7), pady=3)
            ttk.Button(settings, text="…", width=3, command=lambda v=var, k=kind: self._browse(v, k)).grid(row=r, column=2)
        limit_bar = ttk.Frame(settings)
        limit_bar.grid(row=4, column=0, columnspan=3, sticky="w", pady=(7, 0))
        ttk.Label(limit_bar, text="Limite par sonde (s)").pack(side="left")
        ttk.Spinbox(limit_bar, textvariable=self.timeout, from_=1, to=3600, width=7).pack(side="left", padx=(7, 18))
        ttk.Label(limit_bar, text="Budget global (min)").pack(side="left")
        ttk.Spinbox(limit_bar, textvariable=self.budget, from_=1, to=1440, width=7).pack(side="left", padx=(7, 15))
        ttk.Label(limit_bar, text="Maximums de sécurité, pas des durées prévues.", foreground=SLATE).pack(side="left")

        middle = ttk.Frame(main_tab)
        middle.pack(fill="x", expand=False)
        left = ttk.LabelFrame(middle, text=" Langues avec pilotes préparés ", padding=8)
        left.pack(side="left", fill="both", expand=True, padx=(0, 9))
        selection = ttk.Frame(left)
        selection.pack(fill="x", pady=(0, 6))
        self.refresh_button = ttk.Button(selection, text="Détecter", command=self.refresh_catalog)
        self.refresh_button.pack(side="left", padx=(0, 5))
        ttk.Button(selection, text="14 retenues", command=self._select_focus14).pack(side="left", padx=(0, 5))
        ttk.Button(selection, text="20 pilotes", command=self._select_all).pack(side="left", padx=(0, 5))
        ttk.Button(selection, text="Aucun", command=self._select_none).pack(side="left")
        self.tree_count = ttk.Label(selection, text="", foreground=SLATE)
        self.tree_count.pack(side="right")
        columns = ("code", "name", "rgl", "state")
        self.language_tree = ttk.Treeview(left, columns=columns, show="headings", selectmode="extended", height=8)
        for col, name, width in [("code", "Code", 55), ("name", "Langue", 125),
                                  ("rgl", "RGL", 128), ("state", "État", 175)]:
            self.language_tree.heading(col, text=name)
            self.language_tree.column(col, width=width, minwidth=45, stretch=col != "code")
        self.language_tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(left, orient="vertical", command=self.language_tree.yview)
        sb.pack(side="right", fill="y")
        self.language_tree.configure(yscrollcommand=sb.set)
        self.language_tree.bind("<<TreeviewSelect>>", self._selected_count)
        right = ttk.LabelFrame(middle, text=" Campagne ", padding=11)
        right.pack(side="left", fill="y")
        ttk.Label(right, textvariable=self.overview, wraplength=292, justify="left").pack(anchor="w", pady=(0, 10))
        self.buttons: list[ttk.Button] = []
        for title, mode, accent in [("1   Vérifier les profils (sans GF)", "check", False),
                                    ("2   Smoke · 1 sonde / langue", "smoke", False),
                                    ("3   Full · 15 capacités utiles", "full", True)]:
            b = ttk.Button(right, text=title, command=lambda m=mode: self.start(m),
                           style="Accent.TButton" if accent else "TButton")
            b.pack(fill="x", pady=4)
            self.buttons.append(b)
        self.stop_button = ttk.Button(right, text="Arrêter la campagne", command=self.stop, state="disabled")
        self.stop_button.pack(fill="x", pady=(8, 4))
        ttk.Label(right, text="Résultats candidats : revue humaine requise.",
                  foreground=SLATE, justify="left", wraplength=286).pack(anchor="w", pady=(7, 0))
        progress_frame = ttk.Frame(main_tab)
        progress_frame.pack(fill="x", pady=(9, 5))
        ttk.Label(progress_frame, textvariable=self.progress_msg).pack(anchor="w")
        self.progress = ttk.Progressbar(progress_frame, mode="determinate", variable=self.progress_count, maximum=100)
        self.progress.pack(fill="x", pady=(4, 0))
        actions = ttk.Frame(main_tab)
        actions.pack(fill="x", pady=(4, 2))
        ttk.Button(actions, text="Ouvrir les résultats", command=self.open_results).pack(side="left", padx=(0, 7))
        ttk.Button(actions, text="Ouvrir le ZIP produit", command=self.open_zip).pack(side="left", padx=(0, 7))
        ttk.Button(actions, text="Exporter le journal…", command=self.save_log).pack(side="left")
        ttk.Label(actions, text="Aucun gold / RuntimeSet publié", foreground=SLATE).pack(side="right")
        log_frame = ttk.LabelFrame(logs_tab, text=" Journal et verdict ", padding=8)
        log_frame.pack(fill="both", expand=True, pady=(6, 4))
        self.log_text = tk.Text(log_frame, height=9, wrap="word", font=("Consolas", 9),
                                background="#101C2B", foreground="#DCE6F0", relief="flat",
                                insertbackground="white", padx=10, pady=10)
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scroll.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)
        self.log_text.configure(yscrollcommand=log_scroll.set, state="disabled")
        self.log_text.tag_config("warning", foreground="#F6C16F")
        self.log_text.tag_config("success", foreground="#93E7C3")
        ttk.Label(page, textvariable=self.status, foreground=SLATE).pack(anchor="w", pady=(3, 0))

    def _browse(self, variable: tk.StringVar, kind: str) -> None:
        initial = variable.get()
        if kind == "file":
            target = filedialog.askopenfilename(initialdir=str(Path(initial).parent),
                                                title="Sélectionner gf.exe", filetypes=[("Executable", "*.exe"), ("Tous", "*.*")])
        else:
            target = filedialog.askdirectory(initialdir=initial if Path(initial).is_dir() else str(Path.home()),
                                             title="Sélectionner le dossier")
        if target:
            variable.set(target)
            if variable is self.wordbench or variable is self.rgl:
                self.refresh_catalog()

    def _log(self, line: str, tag: str = "") -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", datetime.now().strftime("%H:%M:%S ") + str(line).rstrip("\n") + "\n", tag)
        # Keep the live UI responsive on long campaigns (full logs remain in WordBench reports).
        if int(self.log_text.index("end-1c").split(".")[0]) > 18000:
            self.log_text.delete("1.0", "2001.0")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def refresh_catalog(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        try:
            available, _ = catalog_and_scope(Path(self.wordbench.get()))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.items.clear()
            self.codes.clear()
            self.language_tree.delete(*self.language_tree.get_children())
            self.overview.set("Impossible de lire les profils utiles. Vérifie le dossier WordBench.")
            self._log(f"ERREUR catalogue : {exc}", "warning")
            return
        self.items = {a["code"]: a for a in available}
        self.codes = [a["code"] for a in available]
        self.language_tree.delete(*self.language_tree.get_children())
        for entry in available:
            code = entry["code"]
            if entry["manifest_issue"]:
                state = "Profil incomplet"
            elif not (Path(self.rgl.get()) / "src" / entry["rgl"]).is_dir():
                state = "RGL absente"
            else:
                state = "Pilote préparé"
            self.row_status[code] = state
            self.language_tree.insert("", "end", iid=code,
                                      values=(code, entry["name"], entry["rgl"], state))
        selected = preferred_14_languages(available)
        if selected:
            self.language_tree.selection_set(*selected)
        outside = detected_rgl_codes(Path(self.rgl.get()), set(self.codes))
        self._selected_count()
        self.overview.set(f"{len(selected)}/14 langues retenues présélectionnées; "
                          f"{len(self.codes)} pilotes préparés au total.\n"
                          f"{len(outside)} autres codes RGL hors campagne.\n"
                          "Full : 15 capacités utiles, 5 facultatives exclues.\n"
                          "Vérification systématique avant GF. Résultats non certifiés.")
        self._log(f"Catalogue : {len(selected)} langues du groupe de 14 sélectionnées "
                  f"sur {len(self.codes)} pilotes; {len(outside)} autres RGL sans pilote.")

    def _selected_count(self, _event: object = None) -> None:
        self.tree_count.configure(text=f"{len(self.language_tree.selection())} sélectionnées")

    def _select_none(self) -> None:
        chosen = self.language_tree.selection()
        if chosen:
            self.language_tree.selection_remove(*chosen)
        self._selected_count()

    def _select_focus14(self) -> None:
        selected = preferred_14_languages(list(self.items.values()))
        if selected:
            self.language_tree.selection_set(*selected)
        else:
            self._select_none()
        self._selected_count()

    def _select_all(self) -> None:
        selected = [c for c in self.codes if not self.items[c]["manifest_issue"]]
        self.language_tree.selection_set(*selected)
        self.tree_count.configure(text=f"{len(selected)} sélectionnées")

    def _paths(self) -> tuple[Path, Path, Path, Path]:
        return (Path(self.wordbench.get()).expanduser(), Path(self.gf.get()).expanduser(),
                Path(self.rgl.get()).expanduser(), Path(self.output.get()).expanduser())

    def start(self, mode: str) -> None:
        if self.worker and self.worker.is_alive():
            return
        codes = [c for c in self.codes if c in self.language_tree.selection()]
        if not codes:
            messagebox.showwarning("Sélection vide", "Sélectionne au moins une langue préparée.")
            return
        try:
            wb, gf, rgl, out = self._paths()
            timeout, budget = int(self.timeout.get()), int(self.budget.get())
            check, run = build_commands(wb, codes, mode, gf, rgl, out, timeout, budget)
        except (ValueError, OSError, KeyError, TypeError) as exc:
            messagebox.showerror("Contrôle des paramètres", str(exc))
            self._log("BLOCAGE : " + str(exc), "warning")
            return
        if mode == "full" and not messagebox.askyesno("Confirmer le périmètre utile",
                f"Lancer {len(codes)} langues × 15 scénarios utiles au maximum ?\n\n"
                "Les résultats sont des candidats non certifiés.\n"
                "L'application ne lancera aucune des 5 capacités facultatives."):
            return
        self.stop_event.clear()
        self.active_mode = mode
        self.selected_codes = codes
        self.progress_count.set(0)
        self.progress_msg.set("Préparation / vérification des pilotes...")
        self.status.set("Exécution en cours — conserver la fenêtre ouverte")
        self.last_zip = None
        self.last_dir = None
        for code in codes:
            self._update_row(code, "En attente")
        for b in self.buttons:
            b.configure(state="disabled")
        self.refresh_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self._log(f"DÉPART {mode.upper()} : {', '.join(codes)}", "success")
        self.worker = threading.Thread(target=self._background, args=(wb, out, codes, mode, check, run), daemon=True)
        self.worker.start()

    def _run_process(self, command: list[str], wordbench: Path) -> tuple[int, str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(wordbench / "src") + os.pathsep + env.get("PYTHONPATH", "")
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        opts = {"creationflags": flags} if os.name == "nt" else {"start_new_session": True}
        if self.stop_event.is_set():
            raise RuntimeError("Annulation demandée avant le lancement.")
        proc = subprocess.Popen(command, cwd=str(wordbench), env=env, text=True,
                                encoding="utf-8", errors="replace", bufsize=1,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, **opts)
        self.process = proc
        if self.stop_event.is_set():
            self._terminate_process_tree()
        lines: list[str] = []
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                lines.append(line)
                self.events.put(("line", line.rstrip("\n")))
            code = proc.wait()
        finally:
            if proc.stdout is not None:
                proc.stdout.close()
            if proc.poll() is None:
                self._terminate_process_tree()
            self.process = None
        return code, "".join(lines)

    def _background(self, wb: Path, out: Path, codes: list[str], mode: str,
                    check: list[str], run: list[str] | None) -> None:
        try:
            self.events.put(("phase", "Vérification des 15 scénarios et empreintes…"))
            check_code, check_output = self._run_process(check, wb)
            if self.stop_event.is_set():
                self.events.put(("finished", ("Arrêt demandé; aucune certification.", None, None)))
                return
            try:
                check_data = json.loads(check_output)
            except (ValueError, TypeError) as exc:
                raise RuntimeError("Rapport de pré-vérification illisible : " + str(exc)) from exc
            if check_data.get("schema_id") != "defluens.batch-preflight":
                raise RuntimeError("Schéma inattendu du contrôle WordBench")
            self.events.put(("preflight", check_data))
            if check_code != 0 or check_data.get("ok") is not True:
                raise RuntimeError("Contrôle de conformité échoué. Aucun GF lancé.")
            if run is None:
                self.events.put(("finished", ("Pré-vérification OK — aucun compilateur lancé.", None, None)))
                return
            before = {p.name for p in out.glob(f"defluens-batch-{mode}-*") if p.is_dir()} if out.is_dir() else set()
            if self.stop_event.is_set():
                self.events.put(("finished", ("Arrêt demandé avant lancement GF.", None, None)))
                return
            self.events.put(("phase", f"Campagne GF {mode} en cours…"))
            run_code, _ = self._run_process(run, wb)
            directory, report = load_summary_from_new_run(out, mode, before)
            if self.stop_event.is_set():
                self.events.put(("finished", ("ARRÊTÉE — preuves partielles possibles, non qualifiées.", directory, report)))
            elif report is None:
                raise RuntimeError(f"La commande a retourné {run_code} mais aucun nouveau batch_summary.json n'a été trouvé.")
            else:
                verdict, detail = summarize_campaign(report, codes)
                if run_code != 0 and verdict == "TERMINÉ — CANDIDATS NON CERTIFIÉS":
                    verdict = "ERREUR DE COMMANDE — VÉRIFIER LE RAPPORT"
                self.events.put(("finished", (f"{verdict} · {detail} · code CLI {run_code}", directory, report)))
        except Exception as exc:
            self.events.put(("finished", ("ÉCHEC / BLOCAGE : " + str(exc), None, None)))

    def _update_row(self, code: str, state: str) -> None:
        if self.language_tree.exists(code):
            self.row_status[code] = state
            self.language_tree.set(code, "state", state)

    def _poll(self) -> None:
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "line":
                    line = value
                    self._log(line, "warning" if ("ERREUR" in line or "ERROR" in line or "failed" in line) else "")
                    match = PROGRESS_RE.match(line)
                    if match:
                        n, total, code = match.groups()
                        self.progress_count.set(100 * (int(n) - 1) / max(int(total), 1))
                        self.progress_msg.set(f"Langue {n}/{total} · {code} · {self.active_mode}")
                        self._update_row(code, "GF en cours…")
                    sc = SCENARIO_RE.match(line)
                    if sc:
                        n, total, _sid, s = sc.groups()
                        self.progress_msg.set(f"{self.active_mode} · scénario {n}/{total} : {s}")
                elif kind == "phase":
                    self.progress_msg.set(value)
                    self._log(value, "success")
                elif kind == "preflight":
                    for item in value.get("languages", []):
                        self._update_row(item.get("language", ""),
                                         "Profil vérifié" if item.get("status") == "preflight_ok" else "Échec contrôle")
                elif kind == "finished":
                    msg, directory, report = value
                    self.last_dir = directory
                    if report and directory:
                        path = Path(report.get("archive_path", ""))
                        self.last_zip = path if path.is_file() else None
                        for entry in report.get("entries", []):
                            self._update_row(entry.get("language", ""), entry.get("status", "inconnu"))
                        self.progress_count.set(100 * len(report.get("entries", [])) /
                                                max(len(self.selected_codes), 1))
                    self._log(msg, "warning" if ("BLOCAGE" in msg or "PARTIEL" in msg or "ARRÊTÉE" in msg or "ANOMALIES" in msg) else "success")
                    self.progress_msg.set(msg[:155])
                    self.status.set("Inactif — rapports de développement uniquement")
                    for b in self.buttons:
                        b.configure(state="normal")
                    self.refresh_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    if self.exit_after_cancel:
                        self.root.destroy()
                        return
        except queue.Empty:
            pass
        self.root.after(110, self._poll)

    def stop(self) -> None:
        if not (self.worker and self.worker.is_alive()):
            return
        if not self.stop_event.is_set():
            self.stop_event.set()
            self._log("ARRÊT DEMANDÉ — le processus GF enfant doit être interrompu.", "warning")
            threading.Thread(target=self._terminate_process_tree, daemon=True).start()

    def _terminate_process_tree(self) -> None:
        proc = self.process
        if proc is None or proc.poll() is not None:
            return
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=subprocess.CREATE_NO_WINDOW, timeout=15, check=False)
            else:
                os.killpg(proc.pid, signal.SIGTERM)
        except (OSError, subprocess.SubprocessError):
            try:
                proc.terminate()
            except OSError:
                pass

    def open_results(self) -> None:
        path = Path(self.output.get()).expanduser()
        if path.is_dir():
            if os.name == "nt":
                os.startfile(str(path))
            else:
                messagebox.showinfo("Dossier de résultats", str(path))
        else:
            messagebox.showwarning("Pas encore de résultats", f"Ce dossier n'existe pas : {path}")

    def open_zip(self) -> None:
        if not self.last_zip or not self.last_zip.is_file():
            messagebox.showinfo("ZIP indisponible", "Aucun nouveau ZIP global n'a été produit lors de cette session.")
        elif os.name == "nt":
            os.startfile(str(self.last_zip))
        else:
            messagebox.showinfo("ZIP", str(self.last_zip))

    def save_log(self) -> None:
        filename = filedialog.asksaveasfilename(title="Enregistrer le journal", defaultextension=".txt",
                                                filetypes=[("Texte", "*.txt")])
        if filename:
            try:
                Path(filename).write_text(self.log_text.get("1.0", "end-1c"), encoding="utf-8-sig")
            except OSError as exc:
                messagebox.showerror("Enregistrement impossible", str(exc))

    def _close(self) -> None:
        if self.worker and self.worker.is_alive():
            if messagebox.askyesno("Campagne en cours", "Interrompre la campagne et fermer l'application ?\n"
                                                   "Les résultats partiels seront conservés par WordBench."):
                self.exit_after_cancel = True
                self.stop()
            return
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    try:
        QualificationWindow().run()
    except Exception as exc:
        # Pythonw suppresses stderr: always surface startup errors to the user.
        try:
            fallback = tk.Tk()
            fallback.withdraw()
            messagebox.showerror("Qualification WordBench — erreur de démarrage", str(exc))
            fallback.destroy()
        except Exception:
            pass

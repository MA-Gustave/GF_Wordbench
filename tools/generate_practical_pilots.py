"""Reproduce 15 GF semantic probes for all prepared languages in the catalog.

Run explicitly after editing lexical seeds; regenerating deliberately replaces pilot
sources and changes their SHA-256 locks. Golds are never generated or approved here.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PILOTS = ROOT / 'pilots' / 'practical_generation_v1'
CATALOG = json.loads((PILOTS / 'language_catalog.json').read_text(encoding='utf-8'))
LANGUAGES = {code: (item['rgl_directory'], item['lexical_seeds'])
             for code, item in CATALOG['languages'].items()}

# Every probe isolates one grammatical mechanism. Syntax builders intentionally
# depend on language-specific RGL rather than string-splicing the whole sentence.
# First-pass seed lexemes need a human review for Fre/Sqi (and for idiomatic Eng).
CASES = {
 'factual-present': ('FactualPresent', 'Present factual predicate', 'Mira is ready.', 'mkUtt (mkCl {subj} {ready})'),
 'past-event': ('PastEvent','Completed event','Mira arrived.', 'mkUtt (mkS pastTense (mkCl {subj} {arrive}))'),
 'past-state': ('PastState','Past state','Mira was tired.', 'mkUtt (mkS pastTense (mkCl {subj} {tired}))'),
 'future-reference': ('FutureReference','Future reference','Mira will return.', 'mkUtt (mkS futureTense (mkCl {subj} {return}))'),
 'factual-negation': ('FactualNegation','Negated proposition','Mira is not ready.', 'mkUtt (mkS negativePol (mkCl {subj} {ready}))'),
 'temporal-order': ('TemporalOrder','Temporal ordering','Mira rests after the meeting.', 'mkUtt (mkCl {subj} (mkVP (mkVP {rest}) (Syntax{language}.mkAdv after_Prep (mkNP the_Quant (mkCN {meeting})))))'),
 'condition-real': ('ConditionReal','Real-world condition','If Mira arrives, the device works.', 'mkUtt (mkS (Syntax{language}.mkAdv if_Subj (mkS (mkCl {subj} {arrive}))) (mkS (mkCl {device_np} {work})))'),
 'possibility': ('Possibility','Possibility, not fact','Mira can return.', 'mkUtt (mkCl {subj} (mkVP can_VV (mkVP {return})))'),
 'source-attribution': ('SourceAttribution','Attributed statement','Mira says that the device is ready.', 'mkUtt (mkCl {subj} (mkVS (mkV {say})) (mkS (mkCl {device_np} {ready})))'),
 'quantity': ('Quantity','Explicit quantity','Mira carries two books.', 'mkUtt (mkCl {subj} (mkV2 {carry}) (mkNP n2_Numeral (mkCN {book})))'),
 'location': ('Location','Spatial relationship','Mira is in the house.', 'mkUtt (mkCl {subj} (Syntax{language}.mkAdv in_Prep (mkNP the_Quant (mkCN {house}))))'),
 'instruction': ('Instruction','Positive imperative','Wait!', 'mkUtt (mkImp {wait})'),
 'prohibition': ('Prohibition','Negative imperative','Do not wait!', 'mkUtt negativePol (mkImp {wait})'),
 'obligation': ('Obligation','Obligation distinct from possibility','You must wait.', 'mkUtt (mkCl (mkNP youSg_Pron) (mkVP must_VV (mkVP {wait})))'),
 'conditional-instruction': ('ConditionalInstruction','Instruction linked to a condition','If Mira arrives, wait!', 'mkUtt (mkImp (mkVP (mkVP {wait}) (Syntax{language}.mkAdv if_Subj (mkS (mkCl {subj} {arrive})))))'),
}

def digest(path:Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build(*, root:Path = PILOTS, allow_reset_alignment:bool = False) -> None:
    # Protect previously aligned and SHA-locked pilot sources from an accidental
    # whole-catalog regeneration. Resetting requires an explicit opt-in.
    if not allow_reset_alignment:
        for code in LANGUAGES:
            existing = root / code / 'pilot_manifest.json'
            if existing.is_file() and 'alignment' in json.loads(existing.read_text(encoding='utf-8')):
                raise RuntimeError(
                    f'{code}: alignment already applied; generation would overwrite reviewed proposals. '
                    'Pass allow_reset_alignment=True only when deliberately discarding them.'
                )
    for code, (directory, lex) in LANGUAGES.items():
        base = root / code
        inputs = base / 'validation' / 'inputs'
        scripts = base / 'validation' / 'scenarios'
        gold = base / 'validation' / 'gold'
        for dirpath in (inputs, scripts, gold):
            dirpath.mkdir(parents=True,exist_ok=True)
        manifest = {'schema_id':'defluens.pilot-catalog','schema_version':'1.0',
                    'language_code':code,'rgl_directory':directory,'lexical_seeds_reviewed':False,
                    'gold_approved':False,'lexical_status':CATALOG['languages'][code]['lexical_status'],
                    'scenarios':[]}
        for sid,(name,description,meaning,formula) in CASES.items():
            tag = ''.join(part.title() for part in sid.split('-'))
            abs_name=f'Defluens{tag}'
            cnc_name=f'{abs_name}{code}'
            abs_path=inputs / f'{abs_name}.gf'
            cnc_path=inputs / f'{cnc_name}.gf'
            abs_path.write_text(f'''-- Ars Magna Defluens: {sid} (isolated semantic probe)\nabstract {abs_name} = {{\n  flags startcat = Statement ;\n  cat Statement ;\n  fun Realize : Statement ;\n}}\n''',encoding='utf-8',newline='\n')
            # GF Syntax API + language paradigms: lexical words are provisional
            # and require a native-speaker review before any gold approval.
            words={
               'subj':f'(mkNP (mkPN "{lex["name"]}"))',
               'device_np':f'(mkNP the_Quant (mkCN (mkN "{lex["device"]}")))',
               'ready':f'(mkAP (mkA "{lex["ready"]}"))',
               'tired':f'(mkAP (mkA "{lex["tired"]}"))',
            }
            for key in ('arrive','return','rest','work','wait'):
                words[key]=f'(mkV "{lex[key]}")'
            for key in ('meeting','book','house'):
                words[key]=f'(mkN "{lex[key]}")'
            for key in ('say','carry'):
                words[key]=f'"{lex[key]}"'
            expression = formula.format(language=code, **words)
            cnc_path.write_text(f'''-- Ars Magna Defluens: {sid} -- DRAFT LEXEMES, NOT A GOLD REFERENCE\nconcrete {cnc_name} of {abs_name} = open Syntax{code}, Paradigms{code} in {{\n  lincat Statement = Utt ;\n  lin Realize = {expression} ;\n}}\n''',encoding='utf-8',newline='\n')
            script_path=scripts / f'{sid}.gfs'
            script_path.write_text(f'''-- Semantic pilot {sid}: {description}\n-- Expected meaning (English gloss): {meaning}\n-- GF_WORDBENCH_INPUT_SHA256 {digest(abs_path)} validation/inputs/{abs_path.name}\n-- GF_WORDBENCH_INPUT_SHA256 {digest(cnc_path)} validation/inputs/{cnc_path.name}\ni {cnc_name}.gf\nps "GF_WORDBENCH_BEGIN linearize"\nl -lang={cnc_name} Realize\nps "GF_WORDBENCH_END linearize"\nq\n''',encoding='utf-8',newline='\n')
            manifest['scenarios'].append({'id':sid,'semantic_intent':description,'meaning_en':meaning,
                                          'module':cnc_path.name,'abstract_module':abs_path.name,
                                          'script':f'validation/scenarios/{sid}.gfs','gold':'not-approved',
                                          'source_sha256':digest(cnc_path), 'script_sha256':digest(script_path)})
        # Canonical profile uses RGL language selection from CLI; source-root is
        # read-only selected RGL. Checkpoint convention for each language.
        required = ', '.join(json.dumps(x,ensure_ascii=False) for x in CASES)
        # Valid, portable canonical WordBench project descriptor. The pilot CLI
        # uses its own isolated GF process boundary; the full checkpoint-mode
        # wiring still needs a separate end-to-end integration test with RGL.
        (base/'project.toml').write_text(f'''schema_id = "gf-wordbench.project"
schema_version = "1.0"

[project]
id = "defluens-{code.lower()}-pilot"
name = "Ars Magna Defluens practical pilot — {code}"
language_code = "{directory}"
root = "."

[sources]
directory = "validation/inputs"
glob = "*.gf"
include_regex = "^[A-Z][A-Za-z0-9_]*[.]gf$"
exclude_regex = "[.]bak[.]gf$"

[gf]
path_parts = []
minimum_version = ""

[modules]
entrypoints = ["DefluensFactualPresent{code}.gf"]
checkpoints = ["DefluensFactualPresent{code}.gf"]

[validation]
required_scenarios = [{required}]
optional_scenarios = []
release_requires_pgf = false
''',encoding='utf-8',newline='\n')
        (base/'pilot_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        (base/'README.md').write_text(f'''# Ars Magna Defluens — practical pilot {code}\n\n15 **isolated GF source probes** using RGL `Syntax{code}` and `Paradigms{code}`.\nThe selected language is `gf-rgl/src/{directory}`.\n\nThese are **provisional test materials**, not validated linguistic translations.\nNo `.gold` files are approved. A syntactically compilable probe does not establish\npractical coverage; WordBench must generate real output, a reviewer must assess\neach sentence and approve a canonical gold before status `passed` is justified.\n\nDo not edit GF inputs without regenerating scenario SHA locks using\n`python tools/generate_practical_pilots.py`.\n''',encoding='utf-8',newline='\n')
        (gold/'README.md').write_text('No golds shipped. Review native GF output before creating any .gold files.\n',encoding='utf-8')
        # The stock WordBench validation-profile loader requires an explicit
        # documentation footprint. These are truthful pilot notes, not invented
        # linguistic evidence or claims of completion.
        doc_names = [
            '00_PROJECT_START_HERE__PROJECT_DOCS.md',
            'CATEGORY_AND_LINCAT_CONTRACT.md', 'DECISION_LOG.md',
            'INTERFILE_CONTRACT_LOCK.md', 'KNOWN_ISSUES.md',
            'LANGUAGE_ARCHITECTURE.md', 'LANGUAGE_OVERVIEW.md',
            'MODULE_DEPENDENCY_MAP.md', 'MORPHOLOGY_SPEC.md',
            'RELEASE_CRITERIA__PROJECT_DOCS.md', 'RESEARCH_EVIDENCE.md',
            'STATUS_LEDGER__PROJECT_DOCS.md', 'SYNTAX_AND_CONSTRUCTOR_RULES.md',
            'TEST_COVERAGE_MATRIX__PROJECT_DOCS.md',
            'VALIDATION_SPEC__PROJECT_DOCS.md',
        ]
        docs_dir = base / 'docs'
        docs_dir.mkdir(parents=True,exist_ok=True)
        for doc in doc_names:
            (docs_dir / doc).write_text(
                f'# {doc.removesuffix(".md").replace("_", " ")} — {code}\n\n'
                f'**État : prototype pilote non validé**. 15 constructions sémantiques sont\n'
                f'présentes dans `validation/scenarios`. Elles emploient les sources\n'
                f'RGL `Syntax{code}` et `Paradigms{code}`. Aucune sortie linguistique\n'
                f'n’est encore approuvée ; aucune référence gold n’est fournie.\n\n'
                f'Ce document sera complété lors de la revue de la langue.\n',
                encoding='utf-8',newline='\n')
        for part in (base/'validation'/'README.md', inputs/'README.md', scripts/'README.md'):
            part.write_text(
                f'# Validation pilote {code}\n\n'
                'Sources de test et scripts signés SHA-256 ; non approuvés linguistiquement.\n',
                encoding='utf-8',newline='\n')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reset-alignment', action='store_true',
                        help='DANGER: explicitly discard the existing RGL-aligned pilot files and source locks')
    args = parser.parse_args()
    build(allow_reset_alignment=args.reset_alignment)
    print(f'Generated {len(LANGUAGES)} pilot profiles, {len(CASES)} isolated scenarios each in {PILOTS}')

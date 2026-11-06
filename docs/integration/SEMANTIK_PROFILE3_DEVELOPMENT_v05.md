# Développement du premier PGF pour SemantiK — Defluens v0.5

Lanceur `Lancer_Premier_PGF_SemantiK.bat` ; ou `python tools/build_semantik_profile3_candidate.py --force`.

- **Source d'autorité** : `SemantiK_Architect/profiles/konstellation-explorer-3/` (la grammaire n'est pas réécrite ici).
- **Compilateur** : GF 3.12 véritable, via la construction de commande et le processus isolé GF WordBench.
- **Sortie** : `%USERPROFILE%\Downloads\Ars_Magna_Defluens\semantik_candidates\konstellation-fr-3\`.
- **Preuves** : `grammar.pgf` issu du compilateur, `pipeline.lock.json` contenant les empreintes des cinq artefacts, `build-report.json` et les journaux GF.
- **Portée** : seulement cinq assertions françaises du profil `konstellation-explorer-3`, avec deux opérations SA↔GF (`clause.transitive_event` et `clause.copular_classification`). Cette grammaire de prototype contient encore des réalisations lexicales spécifiques, pas une solution généralisée pour 15 capacités.
- **Statut** : candidat uniquement. Aucune publication, modification d'activation, validation linguistique ou décision de conformité ne découle de ce build.

Après compilation, ouvrir l'Atelier sémantique Defluens v0.5, choisir l'une des cinq demandes du profil et cliquer « Prévisualiser avec le vrai GF ». Cela appelle le chemin candidat officiel SemantiK Architect; aucune sortie simulée n'est autorisée.

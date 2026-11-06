-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: condition-real -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionRealSpa of DefluensConditionReal = open SyntaxSpa, ParadigmsSpa in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS (SyntaxSpa.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira" feminine)) (mkV "llegar")))) (mkS (mkCl (mkNP the_Quant (mkCN (mkN "dispositivo"))) (mkV "funcionar")))) ;
}

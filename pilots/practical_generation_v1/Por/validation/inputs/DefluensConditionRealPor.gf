-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: condition-real -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionRealPor of DefluensConditionReal = open SyntaxPor, ParadigmsPor in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS (SyntaxPor.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira" feminine)) (mkV "chegar")))) (mkS (mkCl (mkNP the_Quant (mkCN (mkN "dispositivo"))) (mkV "funcionar")))) ;
}

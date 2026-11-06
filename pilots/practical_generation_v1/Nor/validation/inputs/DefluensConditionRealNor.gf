-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Defluens lexical stabilization v0.2.1: PROPOSED / GF RE-RUN REQUIRED
-- Ars Magna Defluens: condition-real -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionRealNor of DefluensConditionReal = open SyntaxNor, ParadigmsNor in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS (SyntaxNor.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira" feminine)) (mkV "ankomme")))) (mkS (mkCl (mkNP the_Quant (mkCN (mkN "apparat" neutrum))) (mkV "virke")))) ;
}

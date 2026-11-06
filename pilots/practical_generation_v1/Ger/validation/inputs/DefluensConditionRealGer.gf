-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: condition-real -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionRealGer of DefluensConditionReal = open SyntaxGer, ParadigmsGer in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS (SyntaxGer.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira" feminine)) (mkV "ankommen")))) (mkS (mkCl (mkNP the_Quant (mkCN (mkN "Gerät" neuter))) (mkV "funktionieren")))) ;
}

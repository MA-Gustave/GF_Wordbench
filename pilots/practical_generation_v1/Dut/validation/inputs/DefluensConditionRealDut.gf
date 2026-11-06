-- Defluens lexical stabilization v0.2.1: PROPOSED / GF RE-RUN REQUIRED
-- Ars Magna Defluens: condition-real -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionRealDut of DefluensConditionReal = open SyntaxDut, ParadigmsDut in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS (SyntaxDut.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "aankomen")))) (mkS (mkCl (mkNP the_Quant (mkCN (mkN "apparaat" neuter))) (mkV "werken")))) ;
}

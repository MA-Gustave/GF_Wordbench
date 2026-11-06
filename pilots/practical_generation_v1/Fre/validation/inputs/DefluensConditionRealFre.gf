-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Defluens lexical stabilization v0.2.1: PROPOSED / GF RE-RUN REQUIRED
-- Ars Magna Defluens: condition-real -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionRealFre of DefluensConditionReal = open SyntaxFre, ParadigmsFre in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS (SyntaxFre.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira" feminine)) (mkV "arriver")))) (mkS (mkCl (mkNP the_Quant (mkCN (mkN "dispositif"))) (mkV "fonctionner")))) ;
}

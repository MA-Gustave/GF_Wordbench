-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Defluens lexical stabilization v0.2.1: PROPOSED / GF RE-RUN REQUIRED
-- Ars Magna Defluens: condition-real -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionRealNno of DefluensConditionReal = open SyntaxNno, ParadigmsNno, (I = IrregNno) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS (SyntaxNno.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira" feminine)) (I.komme_V)))) (mkS (mkCl (mkNP the_Quant (mkCN (mkN "apparat" neutrum))) (mkV "verke")))) ;
}

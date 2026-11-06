-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Defluens lexical stabilization v0.2.1: PROPOSED / GF RE-RUN REQUIRED
-- Ars Magna Defluens: temporal-order -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensTemporalOrderNor of DefluensTemporalOrder = open SyntaxNor, ParadigmsNor in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira" feminine)) (mkVP (mkVP (mkV "hvile")) (SyntaxNor.mkAdv after_Prep (mkNP the_Quant (mkCN (mkN "møte" neutrum)))))) ;
}

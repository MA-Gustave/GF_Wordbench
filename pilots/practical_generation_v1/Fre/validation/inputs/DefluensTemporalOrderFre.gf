-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Defluens lexical stabilization v0.2.1: PROPOSED / GF RE-RUN REQUIRED
-- Ars Magna Defluens: temporal-order -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensTemporalOrderFre of DefluensTemporalOrder = open SyntaxFre, ParadigmsFre in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira" feminine)) (mkVP (mkVP (reflV (mkV "reposer"))) (SyntaxFre.mkAdv after_Prep (mkNP the_Quant (mkCN (mkN "réunion" feminine)))))) ;
}

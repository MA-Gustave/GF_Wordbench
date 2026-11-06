-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: source-attribution -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensSourceAttributionAfr of DefluensSourceAttribution = open SyntaxAfr, ParadigmsAfr, (L = LexiconAfr) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira")) L.say_VS (mkS (mkCl (mkNP the_Quant (mkCN (mkN "toestel"))) (mkAP (mkA "gereed"))))) ;
}

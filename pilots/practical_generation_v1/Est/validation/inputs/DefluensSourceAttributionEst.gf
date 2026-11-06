-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: source-attribution -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensSourceAttributionEst of DefluensSourceAttribution = open SyntaxEst, ParadigmsEst, (L = LexiconEst) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira")) L.say_VS (mkS (mkCl (mkNP the_Quant (mkCN (mkN "seade"))) (mkAP L.ready_A)))) ;
}

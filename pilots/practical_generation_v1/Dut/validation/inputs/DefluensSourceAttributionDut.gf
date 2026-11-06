-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Defluens lexical stabilization v0.2.1: PROPOSED / GF RE-RUN REQUIRED
-- Ars Magna Defluens: source-attribution -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensSourceAttributionDut of DefluensSourceAttribution = open SyntaxDut, ParadigmsDut, (L = LexiconDut) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira")) L.say_VS (mkS (mkCl (mkNP the_Quant (mkCN (mkN "apparaat" neuter))) (mkAP L.ready_A)))) ;
}

-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Defluens lexical stabilization v0.2.1: PROPOSED / GF RE-RUN REQUIRED
-- Ars Magna Defluens: source-attribution -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensSourceAttributionDan of DefluensSourceAttribution = open SyntaxDan, ParadigmsDan, (L = LexiconDan) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira")) L.say_VS (mkS (mkCl (mkNP the_Quant (mkCN (mkN "apparat" neutrum))) (mkAP (mkA "klar"))))) ;
}

-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: source-attribution -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensSourceAttributionGer of DefluensSourceAttribution = open SyntaxGer, ParadigmsGer, (L = LexiconGer) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira" feminine)) L.say_VS (mkS (mkCl (mkNP the_Quant (mkCN (mkN "Gerät" neuter))) (mkAP (mkA "bereit"))))) ;
}

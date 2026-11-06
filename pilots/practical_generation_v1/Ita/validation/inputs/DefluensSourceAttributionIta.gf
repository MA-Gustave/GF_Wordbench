-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: source-attribution -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensSourceAttributionIta of DefluensSourceAttribution = open SyntaxIta, ParadigmsIta, (L = LexiconIta) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira" feminine)) L.say_VS (mkS (mkCl (mkNP the_Quant (mkCN (mkN "dispositivo"))) (mkAP L.ready_A)))) ;
}

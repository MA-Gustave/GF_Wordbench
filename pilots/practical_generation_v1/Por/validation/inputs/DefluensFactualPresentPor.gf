-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: factual-present -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensFactualPresentPor of DefluensFactualPresent = open SyntaxPor, ParadigmsPor, (L = LexiconPor) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira" feminine)) (mkAP L.ready_A)) ;
}

-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: factual-present -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensFactualPresentEng of DefluensFactualPresent = open SyntaxEng, ParadigmsEng, (L = LexiconEng) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira")) (mkAP L.ready_A)) ;
}

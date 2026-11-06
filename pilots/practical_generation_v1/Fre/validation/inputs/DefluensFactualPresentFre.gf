-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: factual-present -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensFactualPresentFre of DefluensFactualPresent = open SyntaxFre, ParadigmsFre, (L = LexiconFre) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira" feminine)) (mkAP L.ready_A)) ;
}

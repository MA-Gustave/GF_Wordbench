-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: factual-negation -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensFactualNegationFre of DefluensFactualNegation = open SyntaxFre, ParadigmsFre, (L = LexiconFre) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS negativePol (mkCl (mkNP (mkPN "Mira" feminine)) (mkAP L.ready_A))) ;
}

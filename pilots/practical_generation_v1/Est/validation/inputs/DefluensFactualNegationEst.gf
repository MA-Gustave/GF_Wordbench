-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: factual-negation -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensFactualNegationEst of DefluensFactualNegation = open SyntaxEst, ParadigmsEst, (L = LexiconEst) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS negativePol (mkCl (mkNP (mkPN "Mira")) (mkAP L.ready_A))) ;
}

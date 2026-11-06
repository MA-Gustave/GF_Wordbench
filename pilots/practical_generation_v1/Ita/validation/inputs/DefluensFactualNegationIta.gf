-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: factual-negation -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensFactualNegationIta of DefluensFactualNegation = open SyntaxIta, ParadigmsIta, (L = LexiconIta) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS negativePol (mkCl (mkNP (mkPN "Mira" feminine)) (mkAP L.ready_A))) ;
}

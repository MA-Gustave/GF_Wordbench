-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Defluens lexical stabilization v0.2.1: PROPOSED / GF RE-RUN REQUIRED
-- Ars Magna Defluens: past-event -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensPastEventNno of DefluensPastEvent = open SyntaxNno, ParadigmsNno, (I = IrregNno) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS pastTense (mkCl (mkNP (mkPN "Mira" feminine)) (I.komme_V))) ;
}

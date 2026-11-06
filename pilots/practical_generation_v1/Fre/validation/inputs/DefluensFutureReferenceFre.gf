-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Defluens lexical stabilization v0.2.1: PROPOSED / GF RE-RUN REQUIRED
-- Ars Magna Defluens: future-reference -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensFutureReferenceFre of DefluensFutureReference = open SyntaxFre, ParadigmsFre, (I = IrregFre) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS futureTense (mkCl (mkNP (mkPN "Mira" feminine)) (I.revenir_V))) ;
}

-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Defluens lexical stabilization v0.2.1: PROPOSED / GF RE-RUN REQUIRED
-- Ars Magna Defluens: quantity -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensQuantityGer of DefluensQuantity = open SyntaxGer, ParadigmsGer, (I = IrregGer), (L = LexiconGer) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira" feminine)) (mkV2 I.tragen_V) (mkNP n2_Numeral (mkCN L.book_N))) ;
}

-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: quantity -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensQuantityIta of DefluensQuantity = open SyntaxIta, ParadigmsIta, (L = LexiconIta) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira" feminine)) (mkV2 "portare") (mkNP n2_Numeral (mkCN L.book_N))) ;
}

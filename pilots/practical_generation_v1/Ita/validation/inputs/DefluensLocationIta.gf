-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: location -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensLocationIta of DefluensLocation = open SyntaxIta, ParadigmsIta, (L = LexiconIta) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira" feminine)) (SyntaxIta.mkAdv in_Prep (mkNP the_Quant (mkCN L.house_N)))) ;
}

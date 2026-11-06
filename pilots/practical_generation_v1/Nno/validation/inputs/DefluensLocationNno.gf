-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: location -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensLocationNno of DefluensLocation = open SyntaxNno, ParadigmsNno, (L = LexiconNno) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira" feminine)) (SyntaxNno.mkAdv in_Prep (mkNP the_Quant (mkCN L.house_N)))) ;
}

-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: location -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensLocationFin of DefluensLocation = open SyntaxFin, ParadigmsFin, (L = LexiconFin) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira")) (SyntaxFin.mkAdv in_Prep (mkNP the_Quant (mkCN L.house_N)))) ;
}

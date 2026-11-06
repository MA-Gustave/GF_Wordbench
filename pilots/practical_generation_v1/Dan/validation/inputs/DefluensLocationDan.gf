-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: location -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensLocationDan of DefluensLocation = open SyntaxDan, ParadigmsDan, (L = LexiconDan) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira")) (SyntaxDan.mkAdv in_Prep (mkNP the_Quant (mkCN L.house_N)))) ;
}

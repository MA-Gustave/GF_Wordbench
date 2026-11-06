-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: location -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensLocationSwe of DefluensLocation = open SyntaxSwe, ParadigmsSwe, (L = LexiconSwe) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira")) (SyntaxSwe.mkAdv in_Prep (mkNP the_Quant (mkCN L.house_N)))) ;
}

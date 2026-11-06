-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: location -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensLocationEst of DefluensLocation = open SyntaxEst, ParadigmsEst, (L = LexiconEst) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira")) (SyntaxEst.mkAdv in_Prep (mkNP the_Quant (mkCN L.house_N)))) ;
}

-- Ars Magna Defluens: past-event -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensPastEventPol of DefluensPastEvent = open SyntaxPol, ParadigmsPol in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS pastTense (mkCl (mkNP (mkPN "Mira")) (mkV "przybyć"))) ;
}

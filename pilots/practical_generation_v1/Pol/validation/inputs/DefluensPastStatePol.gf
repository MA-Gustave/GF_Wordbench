-- Ars Magna Defluens: past-state -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensPastStatePol of DefluensPastState = open SyntaxPol, ParadigmsPol in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS pastTense (mkCl (mkNP (mkPN "Mira")) (mkAP (mkA "zmęczony")))) ;
}

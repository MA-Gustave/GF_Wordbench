-- Ars Magna Defluens: past-state -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensPastStateFin of DefluensPastState = open SyntaxFin, ParadigmsFin in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS pastTense (mkCl (mkNP (mkPN "Mira")) (mkAP (mkA "väsynyt")))) ;
}

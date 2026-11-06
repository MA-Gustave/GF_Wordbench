-- Ars Magna Defluens: past-state -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensPastStateGre of DefluensPastState = open SyntaxGre, ParadigmsGre in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS pastTense (mkCl (mkNP (mkPN "Mira")) (mkAP (mkA "κουρασμένος")))) ;
}

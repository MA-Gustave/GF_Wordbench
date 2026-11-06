-- Ars Magna Defluens: past-state -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensPastStateDut of DefluensPastState = open SyntaxDut, ParadigmsDut in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS pastTense (mkCl (mkNP (mkPN "Mira")) (mkAP (mkA "moe")))) ;
}

-- Ars Magna Defluens: past-event -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensPastEventRus of DefluensPastEvent = open SyntaxRus, ParadigmsRus in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS pastTense (mkCl (mkNP (mkPN "Mira")) (mkV "прибыть"))) ;
}

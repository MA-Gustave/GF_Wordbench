-- Ars Magna Defluens: factual-negation -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensFactualNegationRus of DefluensFactualNegation = open SyntaxRus, ParadigmsRus in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS negativePol (mkCl (mkNP (mkPN "Mira")) (mkAP (mkA "готовый")))) ;
}

-- Ars Magna Defluens: factual-negation -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensFactualNegationPol of DefluensFactualNegation = open SyntaxPol, ParadigmsPol in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS negativePol (mkCl (mkNP (mkPN "Mira")) (mkAP (mkA "gotowy")))) ;
}

-- Ars Magna Defluens: condition-real -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionRealPol of DefluensConditionReal = open SyntaxPol, ParadigmsPol in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS (SyntaxPol.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "przybyć")))) (mkS (mkCl (mkNP the_Quant (mkCN (mkN "urządzenie"))) (mkV "działać")))) ;
}

-- Ars Magna Defluens: condition-real -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionRealCze of DefluensConditionReal = open SyntaxCze, ParadigmsCze in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS (SyntaxCze.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "přijít")))) (mkS (mkCl (mkNP the_Quant (mkCN (mkN "zařízení"))) (mkV "fungovat")))) ;
}

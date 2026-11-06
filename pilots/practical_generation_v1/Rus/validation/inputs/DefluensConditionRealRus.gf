-- Ars Magna Defluens: condition-real -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionRealRus of DefluensConditionReal = open SyntaxRus, ParadigmsRus in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS (SyntaxRus.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "прибыть")))) (mkS (mkCl (mkNP the_Quant (mkCN (mkN "устройство"))) (mkV "работать")))) ;
}

-- Ars Magna Defluens: condition-real -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionRealGre of DefluensConditionReal = open SyntaxGre, ParadigmsGre in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS (SyntaxGre.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "φτάνω")))) (mkS (mkCl (mkNP the_Quant (mkCN (mkN "συσκευή"))) (mkV "λειτουργώ")))) ;
}

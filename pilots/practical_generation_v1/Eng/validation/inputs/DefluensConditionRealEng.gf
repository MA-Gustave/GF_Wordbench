-- Ars Magna Defluens: condition-real -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionRealEng of DefluensConditionReal = open SyntaxEng, ParadigmsEng in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS (SyntaxEng.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "arrive")))) (mkS (mkCl (mkNP the_Quant (mkCN (mkN "device"))) (mkV "work")))) ;
}

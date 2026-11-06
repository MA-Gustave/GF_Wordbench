-- Ars Magna Defluens: temporal-order -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensTemporalOrderRus of DefluensTemporalOrder = open SyntaxRus, ParadigmsRus in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira")) (mkVP (mkVP (mkV "отдыхать")) (SyntaxRus.mkAdv after_Prep (mkNP the_Quant (mkCN (mkN "встреча")))))) ;
}

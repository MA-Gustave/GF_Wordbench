-- Ars Magna Defluens: obligation -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensObligationRus of DefluensObligation = open SyntaxRus, ParadigmsRus in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP youSg_Pron) (mkVP must_VV (mkVP (mkV "ждать")))) ;
}

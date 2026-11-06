-- Ars Magna Defluens: conditional-instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionalInstructionRus of DefluensConditionalInstruction = open SyntaxRus, ParadigmsRus in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkVP (mkVP (mkV "ждать")) (SyntaxRus.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "прибыть")))))) ;
}

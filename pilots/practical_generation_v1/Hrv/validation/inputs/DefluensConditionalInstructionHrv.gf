-- Ars Magna Defluens: conditional-instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionalInstructionHrv of DefluensConditionalInstruction = open SyntaxHrv, ParadigmsHrv in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkVP (mkVP (mkV "čekati")) (SyntaxHrv.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "stići")))))) ;
}

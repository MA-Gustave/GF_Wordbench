-- Ars Magna Defluens: conditional-instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionalInstructionCze of DefluensConditionalInstruction = open SyntaxCze, ParadigmsCze in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkVP (mkVP (mkV "čekat")) (SyntaxCze.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "přijít")))))) ;
}

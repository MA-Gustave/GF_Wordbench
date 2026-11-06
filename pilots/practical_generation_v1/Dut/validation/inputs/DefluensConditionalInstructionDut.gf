-- Ars Magna Defluens: conditional-instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionalInstructionDut of DefluensConditionalInstruction = open SyntaxDut, ParadigmsDut in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkVP (mkVP (mkV "wachten")) (SyntaxDut.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "aankomen")))))) ;
}

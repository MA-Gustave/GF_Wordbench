-- Ars Magna Defluens: conditional-instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionalInstructionPol of DefluensConditionalInstruction = open SyntaxPol, ParadigmsPol in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkVP (mkVP (mkV "czekać")) (SyntaxPol.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "przybyć")))))) ;
}

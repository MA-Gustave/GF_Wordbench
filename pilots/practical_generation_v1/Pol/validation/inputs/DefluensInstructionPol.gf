-- Ars Magna Defluens: instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensInstructionPol of DefluensInstruction = open SyntaxPol, ParadigmsPol in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkV "czekać")) ;
}

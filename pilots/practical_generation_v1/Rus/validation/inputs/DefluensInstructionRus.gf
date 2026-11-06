-- Ars Magna Defluens: instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensInstructionRus of DefluensInstruction = open SyntaxRus, ParadigmsRus in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkV "ждать")) ;
}

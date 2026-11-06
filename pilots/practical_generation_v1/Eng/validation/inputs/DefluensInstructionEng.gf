-- Ars Magna Defluens: instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensInstructionEng of DefluensInstruction = open SyntaxEng, ParadigmsEng in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkV "wait")) ;
}

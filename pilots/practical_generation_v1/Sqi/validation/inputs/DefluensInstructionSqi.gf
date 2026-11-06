-- Ars Magna Defluens: instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensInstructionSqi of DefluensInstruction = open SyntaxSqi, ParadigmsSqi in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkV "pres")) ;
}

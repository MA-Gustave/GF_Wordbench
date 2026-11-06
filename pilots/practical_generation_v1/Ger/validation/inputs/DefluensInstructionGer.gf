-- Ars Magna Defluens: instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensInstructionGer of DefluensInstruction = open SyntaxGer, ParadigmsGer in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkV "warten")) ;
}

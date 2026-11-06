-- Ars Magna Defluens: instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensInstructionIta of DefluensInstruction = open SyntaxIta, ParadigmsIta in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkV "aspettare")) ;
}

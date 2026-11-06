-- Ars Magna Defluens: instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensInstructionAfr of DefluensInstruction = open SyntaxAfr, ParadigmsAfr in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkV "wag")) ;
}

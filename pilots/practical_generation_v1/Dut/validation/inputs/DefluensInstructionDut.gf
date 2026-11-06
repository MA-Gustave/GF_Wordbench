-- Ars Magna Defluens: instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensInstructionDut of DefluensInstruction = open SyntaxDut, ParadigmsDut in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkV "wachten")) ;
}

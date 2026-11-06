-- Ars Magna Defluens: conditional-instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionalInstructionEng of DefluensConditionalInstruction = open SyntaxEng, ParadigmsEng in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkVP (mkVP (mkV "wait")) (SyntaxEng.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "arrive")))))) ;
}

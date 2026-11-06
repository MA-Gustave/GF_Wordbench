-- Ars Magna Defluens: conditional-instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionalInstructionSqi of DefluensConditionalInstruction = open SyntaxSqi, ParadigmsSqi in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkVP (mkVP (mkV "pres")) (SyntaxSqi.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "mbërrij")))))) ;
}

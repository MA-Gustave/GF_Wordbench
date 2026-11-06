-- Ars Magna Defluens: conditional-instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionalInstructionGre of DefluensConditionalInstruction = open SyntaxGre, ParadigmsGre in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkVP (mkVP (mkV "περιμένω")) (SyntaxGre.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "φτάνω")))))) ;
}

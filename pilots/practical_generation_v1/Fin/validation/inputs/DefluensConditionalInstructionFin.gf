-- Ars Magna Defluens: conditional-instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionalInstructionFin of DefluensConditionalInstruction = open SyntaxFin, ParadigmsFin in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkVP (mkVP (mkV "odottaa")) (SyntaxFin.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "saapua")))))) ;
}

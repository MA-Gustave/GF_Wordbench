-- Ars Magna Defluens: conditional-instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionalInstructionDan of DefluensConditionalInstruction = open SyntaxDan, ParadigmsDan in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkVP (mkVP (mkV "vente")) (SyntaxDan.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "ankomme")))))) ;
}

-- Ars Magna Defluens: conditional-instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionalInstructionAfr of DefluensConditionalInstruction = open SyntaxAfr, ParadigmsAfr in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkVP (mkVP (mkV "wag")) (SyntaxAfr.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "aankom")))))) ;
}

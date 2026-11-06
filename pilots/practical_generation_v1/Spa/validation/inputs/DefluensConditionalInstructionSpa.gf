-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: conditional-instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionalInstructionSpa of DefluensConditionalInstruction = open SyntaxSpa, ParadigmsSpa in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkVP (mkVP (mkV "esperar")) (SyntaxSpa.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira" feminine)) (mkV "llegar")))))) ;
}

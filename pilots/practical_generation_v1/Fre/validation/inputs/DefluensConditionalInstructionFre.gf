-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: conditional-instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionalInstructionFre of DefluensConditionalInstruction = open SyntaxFre, ParadigmsFre in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkVP (mkVP (mkV "attendre")) (SyntaxFre.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira" feminine)) (mkV "arriver")))))) ;
}

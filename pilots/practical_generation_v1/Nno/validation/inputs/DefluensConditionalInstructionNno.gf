-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Defluens lexical stabilization v0.2.1: PROPOSED / GF RE-RUN REQUIRED
-- Ars Magna Defluens: conditional-instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionalInstructionNno of DefluensConditionalInstruction = open SyntaxNno, ParadigmsNno, (I = IrregNno) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkVP (mkVP (mkV "vente")) (SyntaxNno.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira" feminine)) (I.komme_V)))))) ;
}

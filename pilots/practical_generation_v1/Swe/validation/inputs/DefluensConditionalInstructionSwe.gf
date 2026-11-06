-- Defluens lexical stabilization v0.2.1: PROPOSED / GF RE-RUN REQUIRED
-- Ars Magna Defluens: conditional-instruction -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensConditionalInstructionSwe of DefluensConditionalInstruction = open SyntaxSwe, ParadigmsSwe in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkImp (mkVP (mkVP (mkV "vänta")) (SyntaxSwe.mkAdv if_Subj (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "anlända" "anländer" "anländ" "anlände" "anlänt" "anländ")))))) ;
}

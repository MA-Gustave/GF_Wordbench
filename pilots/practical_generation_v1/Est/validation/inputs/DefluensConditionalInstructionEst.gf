-- Defluens stabilization v0.2.2: imperative + postposed condition.
-- In SentenceEst.ImpVP the VP adverb does not survive linearization;
-- assemble an imperative Utt with a GF-generated conditional Adv instead.
concrete DefluensConditionalInstructionEst of DefluensConditionalInstruction =
  open SyntaxEst, ParadigmsEst, Prelude in {
  lincat Statement = Utt ;
  lin Realize = lin Utt {
    s = (mkUtt (mkImp (mkV "ootama"))).s
        ++ (SyntaxEst.mkAdv if_Subj
              (mkS (mkCl (mkNP (mkPN "Mira")) (mkV "saabuma")))).s
  } ;
}

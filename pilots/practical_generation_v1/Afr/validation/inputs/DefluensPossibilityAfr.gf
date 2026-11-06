-- Defluens stabilization v0.2.3: RGL-typed Afrikaans modal with bare infinitive.
-- The proper name Mira is invariant; verbs remain RGL morphology.
-- Avoid overloaded mkPN inference inside lin Utt, seen in the GF 3.12 log.
concrete DefluensPossibilityAfr of DefluensPossibility =
  open SyntaxAfr, ParadigmsAfr, ResAfr, Prelude in {
  lincat Statement = Utt ;
  oper
    possModal : V = ParadigmsAfr.mkV "kan" ;
    possReturn : V = ParadigmsAfr.mkV "terugkeer" ;
  lin Realize = lin Utt {
    s = "Mira" ++ (possModal.s ! VPres) ++ (possReturn.s ! VInf)
  } ;
}

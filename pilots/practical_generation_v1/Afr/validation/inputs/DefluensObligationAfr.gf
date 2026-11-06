-- Defluens stabilization v0.2.3: RGL-typed Afrikaans modal with bare infinitive.
-- The standard VV composition inserts "te" after "moet"; form the clause with
-- ParadigmsAfr verb forms and the RGL's nominative second-person pronoun.
-- Unlike v0.2.2, avoid overloaded mkNP inside lin Utt (GF type inference issue).
concrete DefluensObligationAfr of DefluensObligation =
  open SyntaxAfr, ParadigmsAfr, ResAfr, Prelude in {
  lincat Statement = Utt ;
  oper
    obligModal : V = ParadigmsAfr.mkV "moet" ;
    obligWait  : V = ParadigmsAfr.mkV "wag" ;
  lin Realize = lin Utt {
    s = youSg_Pron.stressed.nom ++ (obligModal.s ! VPres)
        ++ (obligWait.s ! VInf)
  } ;
}

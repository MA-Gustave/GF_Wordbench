-- Defluens stabilization v0.2.2: Portuguese completed past event.
-- SyntaxPor.pastTense maps to the imperfect in RGL; the RGL ExtendPor
-- defines TPastSimple = {s = []; t = RPasse}. Reuse that exact structure here.
concrete DefluensPastEventPor of DefluensPastEvent =
  open SyntaxPor, ParadigmsPor, CommonRomance, Prelude in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS (lin Tense {s = []; t = RPasse})
    (mkCl (mkNP (mkPN "Mira" feminine)) (mkV "chegar"))) ;
}

-- Defluens stabilization v0.2.2: anterior event with explicit Afrikaans participle.
-- RGL ResAfr has present/past syncretism for ordinary lexical verbs; Anter composes het + VPerf.
concrete DefluensPastEventAfr of DefluensPastEvent = open SyntaxAfr, ParadigmsAfr in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS anteriorAnt
    (mkCl (mkNP (mkPN "Mira")) (mkV "aankom" "aankom" "aangekom"))) ;
}

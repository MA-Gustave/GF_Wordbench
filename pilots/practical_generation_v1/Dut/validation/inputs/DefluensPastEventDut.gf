-- Defluens lexical stabilization v0.2.1: PROPOSED / GF RE-RUN REQUIRED
-- Ars Magna Defluens: past-event -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensPastEventDut of DefluensPastEvent = open SyntaxDut, ParadigmsDut, (I = IrregDut) in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS pastTense (mkCl (mkNP (mkPN "Mira")) (mkV "aan" I.komen_V))) ;
}

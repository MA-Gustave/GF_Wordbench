-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: past-state -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensPastStateGer of DefluensPastState = open SyntaxGer, ParadigmsGer in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkS pastTense (mkCl (mkNP (mkPN "Mira" feminine)) (mkAP (mkA "müde")))) ;
}

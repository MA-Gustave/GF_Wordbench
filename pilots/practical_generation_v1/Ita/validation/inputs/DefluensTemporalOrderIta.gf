-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED
-- Ars Magna Defluens: temporal-order -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensTemporalOrderIta of DefluensTemporalOrder = open SyntaxIta, ParadigmsIta in {
  lincat Statement = Utt ;
  lin Realize = mkUtt (mkCl (mkNP (mkPN "Mira" feminine)) (mkVP (mkVP (mkV "riposare")) (SyntaxIta.mkAdv after_Prep (mkNP the_Quant (mkCN (mkN "riunione" feminine)))))) ;
}

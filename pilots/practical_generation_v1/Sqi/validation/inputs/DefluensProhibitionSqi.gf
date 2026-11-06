-- Ars Magna Defluens: prohibition -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensProhibitionSqi of DefluensProhibition = open SyntaxSqi, ParadigmsSqi in {
  lincat Statement = Utt ;
  lin Realize = mkUtt negativePol (mkImp (mkV "pres")) ;
}

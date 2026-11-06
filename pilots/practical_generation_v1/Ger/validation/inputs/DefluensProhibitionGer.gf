-- Ars Magna Defluens: prohibition -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensProhibitionGer of DefluensProhibition = open SyntaxGer, ParadigmsGer in {
  lincat Statement = Utt ;
  lin Realize = mkUtt negativePol (mkImp (mkV "warten")) ;
}

-- Ars Magna Defluens: prohibition -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensProhibitionIta of DefluensProhibition = open SyntaxIta, ParadigmsIta in {
  lincat Statement = Utt ;
  lin Realize = mkUtt negativePol (mkImp (mkV "aspettare")) ;
}

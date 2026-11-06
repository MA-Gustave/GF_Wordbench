-- Ars Magna Defluens: prohibition -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensProhibitionEng of DefluensProhibition = open SyntaxEng, ParadigmsEng in {
  lincat Statement = Utt ;
  lin Realize = mkUtt negativePol (mkImp (mkV "wait")) ;
}

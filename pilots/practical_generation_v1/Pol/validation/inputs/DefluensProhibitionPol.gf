-- Ars Magna Defluens: prohibition -- DRAFT LEXEMES, NOT A GOLD REFERENCE
concrete DefluensProhibitionPol of DefluensProhibition = open SyntaxPol, ParadigmsPol in {
  lincat Statement = Utt ;
  lin Realize = mkUtt negativePol (mkImp (mkV "czekać")) ;
}

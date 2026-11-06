-- Defluens stabilization v0.2.2: idiomatic negative imperative.
-- Construct the imperative via RGL; add the Afrikaans negative command frame.
concrete DefluensProhibitionAfr of DefluensProhibition =
  open SyntaxAfr, ParadigmsAfr, Prelude in {
  lincat Statement = Utt ;
  lin Realize = lin Utt {
    s = "moenie" ++ (mkUtt (mkImp (mkV "wag"))).s ++ "nie"
  } ;
}

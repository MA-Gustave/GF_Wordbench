-- Ars Magna Defluens: instruction (isolated semantic probe)
abstract DefluensInstruction = {
  flags startcat = Statement ;
  cat Statement ;
  fun Realize : Statement ;
}

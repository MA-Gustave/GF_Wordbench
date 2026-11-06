-- Defluens stabilization v0.2.3: Portuguese future subjunctive.
-- Version 0.2.2 failed because Number/Person constructors Sg/P3 were not opened.
-- CommonRomance extends ParamX, where Sg and P3 are defined.
-- This is a realization-specific tense form, not expanded universal tense coverage.
concrete DefluensConditionalInstructionPor of DefluensConditionalInstruction =
  open SyntaxPor, ParadigmsPor, (B = BeschPor), (C = CommonRomance), Prelude in {
  lincat Statement = Utt ;
  lin Realize = lin Utt {
    s = (mkUtt (mkImp (mkV "esperar"))).s ++ "se"
        ++ (mkUtt (mkNP (mkPN "Mira" feminine))).s
        ++ ((B.chegar_Besch "chegar").s ! (B.VPB (B.Fut B.Sub C.Sg C.P3)))
  } ;
}

module Main (main) where

import ConcernedOntology

assert :: String -> Bool -> IO ()
assert label condition =
  if condition
    then pure ()
    else error ("assertion failed: " <> label)

main :: IO ()
main = do
  assert "guarded syntax is valid" $
    verdictFormalValid (verdict guardedSyntaxBody)
  assert "modular concerned body is valid" $
    verdictFormalValid (verdict modularConcernedBody)
  assert "restless tree is invalid without calibration" $
    not (verdictFormalValid (verdict restlessTreeBody))
  assert "planner without tree remains formally valid but incomplete" $
    verdictFormalValid (verdict plannerWithoutTreeBody)
  assert "shortcut with guard is formally valid" $
    verdictFormalValid (verdict shortcutRewardBody)
  assert "surface reward body is formally valid" $
    verdictFormalValid (verdict surfaceRewardBody)
  assert "passive vector body is formal but module-incomplete" $
    verdictFormalValid (verdict passiveVectorBody)
  assert "restless vector body is invalid without calibration" $
    not (verdictFormalValid (verdict restlessVectorBody))
  assert "syntax memory can bind through causal binding head" $
    verdictFormalValid $
      verdict $
        body
          [ VectorSurfaceEncoder
          , RewardHead
          , CausalBindingHead
          , SyntaxMemory
          , WorldModel
          , InterventionPlanner
          , ConcernPolicy
          , CalibrationGuard
          , FormalGuard
          ]
  assert "rich program composer needs program family head" $
    not $
      verdictFormalValid $
        verdict $
          body
            [ VectorSurfaceEncoder
            , RewardHead
            , WorldModel
            , InterventionPlanner
            , RichProgramComposer
            , FormalGuard
            ]
  assert "rich 2A-v2 body is formally valid" $
    verdictFormalValid $
      verdict $
        body
          [ VectorSurfaceEncoder
          , FlatEncoder
          , RewardHead
          , WorldModel
          , InterventionPlanner
          , CausalBindingHead
          , SyntaxMemory
          , ConcernPolicy
          , CalibrationGuard
          , FormalGuard
          , ProgramFamilyHead
          , RichProgramComposer
          ]

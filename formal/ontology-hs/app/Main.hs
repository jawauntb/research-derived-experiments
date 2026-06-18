module Main (main) where

import ConcernedOntology
import Data.Char (isSpace)
import System.Environment (getArgs)
import System.Exit (die)

main :: IO ()
main = do
  args <- getArgs
  case args of
    [] -> printDefaultSmoke
    ["--motifs", rawMotifs] -> printMotifVerdict rawMotifs
    "--motifs" : _ -> die "usage: ontology-check [body_name ...] | --motifs motif_a,motif_b"
    names -> mapM_ printBodyVerdict names

printDefaultSmoke :: IO ()
printDefaultSmoke = do
  putStrLn "\"guarded_syntax_body\""
  putStrLn (verdictJson (verdict guardedSyntaxBody))
  putStrLn "\"restless_tree_body\""
  putStrLn (verdictJson (verdict restlessTreeBody))
  putStrLn "\"modular_concerned_body\""
  putStrLn (verdictJson (verdict modularConcernedBody))

printBodyVerdict :: String -> IO ()
printBodyVerdict name =
  case bodyByName name of
    Just candidate -> putStrLn (namedVerdictJson name (verdict candidate))
    Nothing -> die ("unknown body: " <> name)

printMotifVerdict :: String -> IO ()
printMotifVerdict rawMotifs =
  case traverse motifByName motifNames of
    Just motifs -> putStrLn (namedVerdictJson "custom_motifs" (verdict (body motifs)))
    Nothing -> die ("unknown motif in: " <> rawMotifs)
  where
    motifNames = filter (not . null) (map trim (splitComma rawMotifs))

bodyByName :: String -> Maybe Body
bodyByName name =
  lookup
    name
    [ ("guarded_syntax_body", guardedSyntaxBody)
    , ("planner_without_tree_body", plannerWithoutTreeBody)
    , ("restless_tree_body", restlessTreeBody)
    , ("shortcut_reward_body", shortcutRewardBody)
    , ("modular_concerned_body", modularConcernedBody)
    , ("surface_reward_body", surfaceRewardBody)
    , ("passive_vector_body", passiveVectorBody)
    , ("restless_vector_body", restlessVectorBody)
    ]

motifByName :: String -> Maybe Motif
motifByName name =
  lookup
    name
    [ ("flat_encoder", FlatEncoder)
    , ("reward_head", RewardHead)
    , ("shortcut_reward_head", ShortcutRewardHead)
    , ("tree_binder", TreeBinder)
    , ("syntax_memory", SyntaxMemory)
    , ("world_model", WorldModel)
    , ("intervention_planner", InterventionPlanner)
    , ("role_specific_heads", RoleSpecificHeads)
    , ("counterfactual_rollout", CounterfactualRollout)
    , ("formal_guard", FormalGuard)
    , ("self_repair", SelfRepair)
    , ("vector_surface_encoder", VectorSurfaceEncoder)
    , ("causal_binding_head", CausalBindingHead)
    , ("concern_policy", ConcernPolicy)
    , ("calibration_guard", CalibrationGuard)
    , ("program_family_head", ProgramFamilyHead)
    , ("rich_program_composer", RichProgramComposer)
    ]

namedVerdictJson :: String -> Verdict -> String
namedVerdictJson name result =
  case verdictJson result of
    '{' : rest -> "{\"body\":" <> quote name <> "," <> rest
    other -> "{\"body\":" <> quote name <> ",\"verdict\":" <> other <> "}"

splitComma :: String -> [String]
splitComma "" = []
splitComma value =
  case break (== ',') value of
    (chunk, "") -> [chunk]
    (chunk, _ : rest) -> chunk : splitComma rest

trim :: String -> String
trim = dropWhileEnd isSpace . dropWhile isSpace

dropWhileEnd :: (a -> Bool) -> [a] -> [a]
dropWhileEnd predicate = reverse . dropWhile predicate . reverse

quote :: String -> String
quote value = "\"" <> concatMap escape value <> "\""

escape :: Char -> String
escape '"' = "\\\""
escape '\\' = "\\\\"
escape char = [char]

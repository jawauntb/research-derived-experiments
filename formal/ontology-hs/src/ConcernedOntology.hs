module ConcernedOntology
  ( Motif (..)
  , Body
  , Violation (..)
  , Verdict (..)
  , body
  , guardedSyntaxBody
  , restlessTreeBody
  , shortcutRewardBody
  , plannerWithoutTreeBody
  , modularConcernedBody
  , surfaceRewardBody
  , passiveVectorBody
  , restlessVectorBody
  , resourceCost
  , violations
  , verdict
  , verdictJson
  ) where

import Data.List (intercalate)
import qualified Data.Set as Set

data Motif
  = FlatEncoder
  | RewardHead
  | ShortcutRewardHead
  | TreeBinder
  | SyntaxMemory
  | WorldModel
  | InterventionPlanner
  | RoleSpecificHeads
  | CounterfactualRollout
  | FormalGuard
  | SelfRepair
  | VectorSurfaceEncoder
  | CausalBindingHead
  | ConcernPolicy
  | CalibrationGuard
  | ProgramFamilyHead
  | RichProgramComposer
  deriving (Bounded, Enum, Eq, Ord, Show)

newtype Body = Body (Set.Set Motif)
  deriving (Eq, Show)

data Violation
  = Missing Motif Motif
  | ShortcutWithoutFormalGuard
  | RestlessWithoutCalibrationGuard
  | ResourceOverBudget Int
  | MissingInputBody
  deriving (Eq, Show)

data Verdict = Verdict
  { verdictFormalValid :: Bool
  , verdictResourceCost :: Int
  , verdictViolations :: [Violation]
  }
  deriving (Eq, Show)

maxResource :: Int
maxResource = 12

body :: [Motif] -> Body
body = Body . Set.fromList

has :: Body -> Motif -> Bool
has (Body motifs) motif = Set.member motif motifs

resourceCost :: Body -> Int
resourceCost (Body motifs) = sum (map motifCost (Set.toList motifs))

motifCost :: Motif -> Int
motifCost motif =
  case motif of
    FlatEncoder -> 1
    RewardHead -> 1
    ShortcutRewardHead -> 1
    TreeBinder -> 2
    SyntaxMemory -> 1
    WorldModel -> 2
    InterventionPlanner -> 2
    RoleSpecificHeads -> 2
    CounterfactualRollout -> 2
    FormalGuard -> 1
    SelfRepair -> 1
    VectorSurfaceEncoder -> 1
    CausalBindingHead -> 1
    ConcernPolicy -> 0
    CalibrationGuard -> 0
    ProgramFamilyHead -> 1
    RichProgramComposer -> 1

dependencies :: [(Motif, [Motif])]
dependencies =
  [ (InterventionPlanner, [WorldModel])
  , (CounterfactualRollout, [WorldModel, InterventionPlanner])
  , (SelfRepair, [FormalGuard])
  , (CausalBindingHead, [VectorSurfaceEncoder])
  , (ConcernPolicy, [WorldModel])
  , (CalibrationGuard, [FormalGuard, ConcernPolicy])
  , (ProgramFamilyHead, [WorldModel])
  , (RichProgramComposer, [InterventionPlanner, ProgramFamilyHead])
  ]

violations :: Body -> [Violation]
violations candidate =
  dependencyViolations
    <> roleHeadViolation
    <> syntaxMemoryViolation
    <> shortcutViolation
    <> restlessViolation
    <> budgetViolation
    <> inputViolation
  where
    dependencyViolations =
      [ Missing motif dep
      | (motif, deps) <- dependencies
      , has candidate motif
      , dep <- deps
      , not (has candidate dep)
      ]
    roleHeadViolation =
      [ Missing RoleSpecificHeads TreeBinder
      | has candidate RoleSpecificHeads
      , not (has candidate TreeBinder)
      , not (has candidate CausalBindingHead)
      ]
    syntaxMemoryViolation =
      [ Missing SyntaxMemory TreeBinder
      | has candidate SyntaxMemory
      , not (has candidate TreeBinder)
      , not (has candidate CausalBindingHead)
      ]
    shortcutViolation =
      [ ShortcutWithoutFormalGuard
      | has candidate ShortcutRewardHead
      , not (has candidate FormalGuard)
      ]
    restlessViolation =
      [ RestlessWithoutCalibrationGuard
      | (has candidate TreeBinder && has candidate InterventionPlanner)
          || (has candidate CausalBindingHead && has candidate ConcernPolicy)
      , not (has candidate CalibrationGuard)
      ]
    cost = resourceCost candidate
    budgetViolation =
      [ ResourceOverBudget cost
      | cost > maxResource
      ]
    inputViolation =
      [ MissingInputBody
      | not (has candidate FlatEncoder)
      , not (has candidate VectorSurfaceEncoder)
      ]

verdict :: Body -> Verdict
verdict candidate =
  Verdict
    { verdictFormalValid = null found
    , verdictResourceCost = resourceCost candidate
    , verdictViolations = found
    }
  where
    found = violations candidate

guardedSyntaxBody :: Body
guardedSyntaxBody =
  body
    [ FlatEncoder
    , RewardHead
    , TreeBinder
    , SyntaxMemory
    , WorldModel
    , InterventionPlanner
    , RoleSpecificHeads
    , FormalGuard
    , ConcernPolicy
    , CalibrationGuard
    ]

plannerWithoutTreeBody :: Body
plannerWithoutTreeBody =
  body
    [ FlatEncoder
    , RewardHead
    , WorldModel
    , InterventionPlanner
    , ConcernPolicy
    ]

restlessTreeBody :: Body
restlessTreeBody =
  body
    [ FlatEncoder
    , RewardHead
    , TreeBinder
    , SyntaxMemory
    , WorldModel
    , InterventionPlanner
    , RoleSpecificHeads
    , FormalGuard
    ]

shortcutRewardBody :: Body
shortcutRewardBody =
  body
    [ FlatEncoder
    , RewardHead
    , ShortcutRewardHead
    , FormalGuard
    ]

modularConcernedBody :: Body
modularConcernedBody =
  body
    [ VectorSurfaceEncoder
    , RewardHead
    , WorldModel
    , ConcernPolicy
    , CausalBindingHead
    , RoleSpecificHeads
    , FormalGuard
    , CalibrationGuard
    ]

surfaceRewardBody :: Body
surfaceRewardBody =
  body
    [ VectorSurfaceEncoder
    , RewardHead
    , ShortcutRewardHead
    , FormalGuard
    ]

passiveVectorBody :: Body
passiveVectorBody =
  body
    [ VectorSurfaceEncoder
    , RewardHead
    , CausalBindingHead
    ]

restlessVectorBody :: Body
restlessVectorBody =
  body
    [ VectorSurfaceEncoder
    , RewardHead
    , WorldModel
    , ConcernPolicy
    , CausalBindingHead
    , FormalGuard
    ]

motifName :: Motif -> String
motifName motif =
  case motif of
    FlatEncoder -> "flat_encoder"
    RewardHead -> "reward_head"
    ShortcutRewardHead -> "shortcut_reward_head"
    TreeBinder -> "tree_binder"
    SyntaxMemory -> "syntax_memory"
    WorldModel -> "world_model"
    InterventionPlanner -> "intervention_planner"
    RoleSpecificHeads -> "role_specific_heads"
    CounterfactualRollout -> "counterfactual_rollout"
    FormalGuard -> "formal_guard"
    SelfRepair -> "self_repair"
    VectorSurfaceEncoder -> "vector_surface_encoder"
    CausalBindingHead -> "causal_binding_head"
    ConcernPolicy -> "concern_policy"
    CalibrationGuard -> "calibration_guard"
    ProgramFamilyHead -> "program_family_head"
    RichProgramComposer -> "rich_program_composer"

violationName :: Violation -> String
violationName violation =
  case violation of
    Missing motif dep -> motifName motif <> "_missing_" <> motifName dep
    ShortcutWithoutFormalGuard -> "shortcut_without_formal_guard"
    RestlessWithoutCalibrationGuard -> "restless_without_calibration_guard"
    ResourceOverBudget cost -> "resource_over_budget_" <> show cost
    MissingInputBody -> "missing_input_body"

verdictJson :: Verdict -> String
verdictJson result =
  "{"
    <> "\"formal_valid\":"
    <> boolJson (verdictFormalValid result)
    <> ",\"resource_cost\":"
    <> show (verdictResourceCost result)
    <> ",\"violations\":["
    <> intercalate "," (map (quote . violationName) (verdictViolations result))
    <> "]}"

boolJson :: Bool -> String
boolJson True = "true"
boolJson False = "false"

quote :: String -> String
quote value = "\"" <> concatMap escape value <> "\""

escape :: Char -> String
escape '"' = "\\\""
escape '\\' = "\\\\"
escape char = [char]

module Main (main) where

import ConcernedOntology

main :: IO ()
main = do
  putStrLn "\"guarded_syntax_body\""
  putStrLn (verdictJson (verdict guardedSyntaxBody))
  putStrLn "\"restless_tree_body\""
  putStrLn (verdictJson (verdict restlessTreeBody))
  putStrLn "\"modular_concerned_body\""
  putStrLn (verdictJson (verdict modularConcernedBody))

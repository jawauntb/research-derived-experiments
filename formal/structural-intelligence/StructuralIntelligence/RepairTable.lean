set_option maxRecDepth 4000000
set_option maxHeartbeats 16000000

/-!
# Structural Intelligence — Representation Repair RR-1 (lift table)

Honesty.  This file banks Theorem RR-1 (Lift table is well-defined) from
`papers/representation_repair_calculus/` on the eight registered witness
worlds of `experiments/representation_repair_pair/core.py`.  For each
canonical row we kernel-check three finite facts on the registered toy:
the broken representation **misses** the target invariant, the lifted
representation **captures** it, and the lift is **minimal** (every
nonempty proper subset of the added components fails to capture).

**Banked:** existence + minimality of repairing lifts on the registered
finite toys, case-by-case, mirroring the Python instrument exactly
(same state lists, invariants, broken/lifted feature maps, and
exhaustive drop-set minimality).

**Withheld / not claimed:** uniqueness of lifts (two minimal lifts may
exist; the calculus records one canonical witness per row), any
continuum or measure-theoretic lift, and composition (RR-2 lives in
`RepresentationRepair.lean`).

**Mathematical claim card**

* **Objects:** finite state lists `S`, target invariants `I : S → V`,
  broken reps `R : S → T_b`, lifted reps `R' : S → T_ℓ` with
  `R` embedded in `R'` (broken features kept).
* **Claim (RR-1):** on each registered row, `R` misses `I`, `R'` captures
  `I`, and every strict subset of the added components of `R'` yields a
  rep that misses `I`.
* **Assumptions:** states and feature maps match the Python instrument;
  capture = functional factorisation (`rep s = rep s' → I s = I s'`);
  minimality = exhaustive over all nonempty subsets of added components.
* **Edge cases:** row worlds range from 6 to 16 states; row 7 uses
  finite protocol/module tags; no scaling reductions were needed (all
  worlds fit kernel `decide` at registered size).

No Mathlib.  No `native_decide`.  Kernel `decide` only.
-/

namespace StructuralIntelligence
namespace RepairTable

/-! ## Core finite predicates (mirroring `core.py`) -/

/-- `I` **captures through** `rep` on `states`: equal feature-tuples
    imply equal invariant values (functional factorisation). -/
def capturesInvariant {S Inv Rep : Type}
    [DecidableEq Inv] [DecidableEq Rep]
    (states : List S) (rep : S → Rep) (inv : S → Inv) : Bool :=
  states.all fun s =>
    states.all fun s' =>
      !(decide (rep s = rep s')) || decide (inv s = inv s')

/-- `I` is **missed** by `rep`: some collision on `rep` separates under `I`. -/
def missesInvariant {S Inv Rep : Type}
    [DecidableEq Inv] [DecidableEq Rep]
    (states : List S) (rep : S → Rep) (inv : S → Inv) : Bool :=
  !capturesInvariant states rep inv

/-! ## Row index -/

inductive RowId where
  | scalarToOperator
  | globalNormToLocalizedMeasure
  | quotientToRestoredFiber
  | staticToPathSpace
  | affineToProjective
  | pointToEnsemble
  | nonComposingToInterface
  | symmetryToGaugeFix
deriving DecidableEq, Repr

def allRows : List RowId :=
  [.scalarToOperator, .globalNormToLocalizedMeasure,
   .quotientToRestoredFiber, .staticToPathSpace,
   .affineToProjective, .pointToEnsemble,
   .nonComposingToInterface, .symmetryToGaugeFix]

/-! ## Row 1: scalar → operator (Pauli / Bloch) -/

inductive PauliState where
  | s0 | s1 | sPlus | sMinus | sI | sIMinus
deriving DecidableEq, Repr

def pauliStates : List PauliState :=
  [.s0, .s1, .sPlus, .sMinus, .sI, .sIMinus]

def pauliInv (s : PauliState) : Int × Int × Int :=
  match s with
  | .s0 => (0, 0, 1)
  | .s1 => (0, 0, -1)
  | .sPlus => (1, 0, 0)
  | .sMinus => (-1, 0, 0)
  | .sI => (0, 1, 0)
  | .sIMinus => (0, -1, 0)

def pauliZ (s : PauliState) : Int := (pauliInv s).2.2
def pauliX (s : PauliState) : Int := (pauliInv s).1
def pauliY (s : PauliState) : Int := (pauliInv s).2.1

def pauliBroken (s : PauliState) : Int := pauliZ s
def pauliLifted (s : PauliState) : Int × Int × Int := (pauliZ s, pauliX s, pauliY s)

def pauliDropX (s : PauliState) : Int × Int := (pauliZ s, pauliY s)
def pauliDropY (s : PauliState) : Int × Int := (pauliZ s, pauliX s)

def pauliMinimal : Bool :=
  missesInvariant pauliStates pauliDropX pauliInv &&
  missesInvariant pauliStates pauliDropY pauliInv &&
  missesInvariant pauliStates pauliBroken pauliInv

theorem row_scalar_broken_misses :
    missesInvariant pauliStates pauliBroken pauliInv = true := by decide

theorem row_scalar_lifted_captures :
    capturesInvariant pauliStates pauliLifted pauliInv = true := by decide

theorem row_scalar_minimal : pauliMinimal = true := by decide

/-! ## Row 2: global norm → localized measure -/

inductive GridState where | s1 | s2 | s3 | s4 | s5 | s6
deriving DecidableEq, Repr

def gridStates : List GridState :=
  [.s1, .s2, .s3, .s4, .s5, .s6]

def gridProfile : GridState → Nat × Nat × Nat
  | .s1 => (1, 5, 7)
  | .s2 => (2, 5, 7)
  | .s3 => (3, 1, 7)
  | .s4 => (3, 2, 7)
  | .s5 => (5, 5, 1)
  | .s6 => (5, 5, 2)

def gridInv (s : GridState) : Nat × Nat × Nat := gridProfile s

def gridSupport (s : GridState) : Nat :=
  let p := gridProfile s
  (if p.1 ≠ 0 then 1 else 0) + (if p.2.1 ≠ 0 then 1 else 0) + (if p.2.2 ≠ 0 then 1 else 0)

def gridM0 (s : GridState) : Nat := (gridProfile s).1
def gridM1 (s : GridState) : Nat := (gridProfile s).2.1
def gridM2 (s : GridState) : Nat := (gridProfile s).2.2

def gridBroken (s : GridState) : Nat := gridSupport s
def gridLifted (s : GridState) : Nat × Nat × Nat × Nat :=
  (gridSupport s, gridM0 s, gridM1 s, gridM2 s)

def gridDropM0 (s : GridState) : Nat × Nat × Nat := (gridSupport s, gridM1 s, gridM2 s)
def gridDropM1 (s : GridState) : Nat × Nat × Nat := (gridSupport s, gridM0 s, gridM2 s)
def gridDropM2 (s : GridState) : Nat × Nat × Nat := (gridSupport s, gridM0 s, gridM1 s)
def gridDropM0M1 (s : GridState) : Nat × Nat := (gridSupport s, gridM2 s)
def gridDropM0M2 (s : GridState) : Nat × Nat := (gridSupport s, gridM1 s)
def gridDropM1M2 (s : GridState) : Nat × Nat := (gridSupport s, gridM0 s)

def gridMinimal : Bool :=
  missesInvariant gridStates gridDropM0 gridInv &&
  missesInvariant gridStates gridDropM1 gridInv &&
  missesInvariant gridStates gridDropM2 gridInv &&
  missesInvariant gridStates gridDropM0M1 gridInv &&
  missesInvariant gridStates gridDropM0M2 gridInv &&
  missesInvariant gridStates gridDropM1M2 gridInv &&
  missesInvariant gridStates gridBroken gridInv

theorem row_grid_broken_misses :
    missesInvariant gridStates gridBroken gridInv = true := by decide

theorem row_grid_lifted_captures :
    capturesInvariant gridStates gridLifted gridInv = true := by decide

theorem row_grid_minimal : gridMinimal = true := by decide

/-! ## Row 3: quotient → restored fiber -/

structure Fiber3 where
  z : Bool
  x : Bool
  y : Bool
deriving DecidableEq, Repr

def fiberStates : List Fiber3 :=
  [⟨false,false,false⟩, ⟨false,false,true⟩, ⟨false,true,false⟩, ⟨false,true,true⟩,
   ⟨true,false,false⟩, ⟨true,false,true⟩, ⟨true,true,false⟩, ⟨true,true,true⟩]

def fiberInv (s : Fiber3) : Fiber3 := s
def fiberZ (s : Fiber3) : Bool := s.z
def fiberX (s : Fiber3) : Bool := s.x
def fiberY (s : Fiber3) : Bool := s.y

def fiberBroken (s : Fiber3) : Bool := fiberZ s
def fiberLifted (s : Fiber3) : Bool × Bool × Bool := (fiberZ s, fiberX s, fiberY s)

def fiberDropX (s : Fiber3) : Bool × Bool := (fiberZ s, fiberY s)
def fiberDropY (s : Fiber3) : Bool × Bool := (fiberZ s, fiberX s)

def fiberMinimal : Bool :=
  missesInvariant fiberStates fiberDropX fiberInv &&
  missesInvariant fiberStates fiberDropY fiberInv &&
  missesInvariant fiberStates fiberBroken fiberInv

theorem row_fiber_broken_misses :
    missesInvariant fiberStates fiberBroken fiberInv = true := by decide

theorem row_fiber_lifted_captures :
    capturesInvariant fiberStates fiberLifted fiberInv = true := by decide

theorem row_fiber_minimal : fiberMinimal = true := by decide

/-! ## Row 4: static → path space -/

def pathStates : List Fiber3 := fiberStates

def pathInv (s : Fiber3) : Fiber3 := s
def pathCurrent (s : Fiber3) : Bool := s.y
def pathT0 (s : Fiber3) : Bool := s.z
def pathT1 (s : Fiber3) : Bool := s.x

def pathBroken (s : Fiber3) : Bool := pathCurrent s
def pathLifted (s : Fiber3) : Bool × Bool × Bool :=
  (pathCurrent s, pathT0 s, pathT1 s)

def pathDropT0 (s : Fiber3) : Bool × Bool := (pathCurrent s, pathT1 s)
def pathDropT1 (s : Fiber3) : Bool × Bool := (pathCurrent s, pathT0 s)

def pathMinimal : Bool :=
  missesInvariant pathStates pathDropT0 pathInv &&
  missesInvariant pathStates pathDropT1 pathInv &&
  missesInvariant pathStates pathBroken pathInv

theorem row_path_broken_misses :
    missesInvariant pathStates pathBroken pathInv = true := by decide

theorem row_path_lifted_captures :
    capturesInvariant pathStates pathLifted pathInv = true := by decide

theorem row_path_minimal : pathMinimal = true := by decide

/-! ## Row 5: affine → projective -/

structure Proj3 where
  a : Nat
  b : Nat
  c : Nat
deriving DecidableEq, Repr

def projStates : List Proj3 :=
  [⟨1,0,1⟩, ⟨0,1,1⟩, ⟨2,3,1⟩, ⟨2,3,0⟩, ⟨5,0,1⟩, ⟨2,5,1⟩]

def projInv (s : Proj3) : Proj3 := s
def projA (s : Proj3) : Nat := s.a
def projB (s : Proj3) : Nat := s.b
def projC (s : Proj3) : Nat := s.c

def projBroken (s : Proj3) : Nat × Nat := (projA s, projB s)
def projLifted (s : Proj3) : Nat × Nat × Nat := (projA s, projB s, projC s)

def projMinimal : Bool :=
  missesInvariant projStates projBroken projInv

theorem row_proj_broken_misses :
    missesInvariant projStates projBroken projInv = true := by decide

theorem row_proj_lifted_captures :
    capturesInvariant projStates projLifted projInv = true := by decide

theorem row_proj_minimal : projMinimal = true := by decide

/-! ## Row 6: point → ensemble -/

structure Ens3 where
  mean : Bool
  var : Bool
  skew : Bool
deriving DecidableEq, Repr

def ensStates : List Ens3 :=
  [⟨false,false,false⟩, ⟨false,false,true⟩, ⟨false,true,false⟩, ⟨false,true,true⟩,
   ⟨true,false,false⟩, ⟨true,false,true⟩, ⟨true,true,false⟩, ⟨true,true,true⟩]

def ensInv (s : Ens3) : Ens3 := s
def ensMean (s : Ens3) : Bool := s.mean
def ensVar (s : Ens3) : Bool := s.var
def ensSkew (s : Ens3) : Bool := s.skew

def ensBroken (s : Ens3) : Bool := ensMean s
def ensLifted (s : Ens3) : Bool × Bool × Bool := (ensMean s, ensVar s, ensSkew s)

def ensDropVar (s : Ens3) : Bool × Bool := (ensMean s, ensSkew s)
def ensDropSkew (s : Ens3) : Bool × Bool := (ensMean s, ensVar s)

def ensMinimal : Bool :=
  missesInvariant ensStates ensDropVar ensInv &&
  missesInvariant ensStates ensDropSkew ensInv &&
  missesInvariant ensStates ensBroken ensInv

theorem row_ens_broken_misses :
    missesInvariant ensStates ensBroken ensInv = true := by decide

theorem row_ens_lifted_captures :
    capturesInvariant ensStates ensLifted ensInv = true := by decide

theorem row_ens_minimal : ensMinimal = true := by decide

/-! ## Row 7: non-composing → interface -/

inductive ModuleTag where | P | Q
deriving DecidableEq, Repr

inductive FamilyTag where | json | grpc
deriving DecidableEq, Repr

structure Iface4 where
  m1 : ModuleTag
  m2 : ModuleTag
  family : FamilyTag
  version : Nat
deriving DecidableEq, Repr

def allModules : List ModuleTag := [.P, .Q]
def allFamilies : List FamilyTag := [.json, .grpc]
def allVersions : List Nat := [1, 2]

def ifaceStatesFull : List Iface4 :=
  allModules.flatMap fun m1 =>
    allModules.flatMap fun m2 =>
      allFamilies.flatMap fun family =>
        allVersions.map fun version => ⟨m1, m2, family, version⟩

def ifaceInv (s : Iface4) : Iface4 := s
def ifaceM1 (s : Iface4) : ModuleTag := s.m1
def ifaceM2 (s : Iface4) : ModuleTag := s.m2
def ifaceFamily (s : Iface4) : FamilyTag := s.family
def ifaceVersion (s : Iface4) : Nat := s.version

def ifaceBroken (s : Iface4) : ModuleTag × ModuleTag := (ifaceM1 s, ifaceM2 s)
def ifaceLifted (s : Iface4) : ModuleTag × ModuleTag × FamilyTag × Nat :=
  (ifaceM1 s, ifaceM2 s, ifaceFamily s, ifaceVersion s)

def ifaceDropFamily (s : Iface4) : ModuleTag × ModuleTag × Nat :=
  (ifaceM1 s, ifaceM2 s, ifaceVersion s)
def ifaceDropVersion (s : Iface4) : ModuleTag × ModuleTag × FamilyTag :=
  (ifaceM1 s, ifaceM2 s, ifaceFamily s)

def ifaceMinimal : Bool :=
  missesInvariant ifaceStatesFull ifaceDropFamily ifaceInv &&
  missesInvariant ifaceStatesFull ifaceDropVersion ifaceInv &&
  missesInvariant ifaceStatesFull ifaceBroken ifaceInv

theorem row_iface_broken_misses :
    missesInvariant ifaceStatesFull ifaceBroken ifaceInv = true := by decide

theorem row_iface_lifted_captures :
    capturesInvariant ifaceStatesFull ifaceLifted ifaceInv = true := by decide

theorem row_iface_minimal : ifaceMinimal = true := by decide

/-! ## Row 8: symmetry → gauge-fix -/

structure Gauge3 where
  a : Int
  b : Int
  c : Int
deriving DecidableEq, Repr

def gaugeStates : List Gauge3 :=
  [⟨0,1,2⟩, ⟨1,2,3⟩, ⟨0,2,1⟩, ⟨5,7,6⟩, ⟨0,0,0⟩, ⟨0,1,1⟩]

def gaugeInv (s : Gauge3) : Int × Int := (s.a - s.b, s.a - s.c)
def gaugeA (s : Gauge3) : Int := s.a
def gaugeAb (s : Gauge3) : Int := s.a - s.b
def gaugeAc (s : Gauge3) : Int := s.a - s.c

def gaugeBroken (s : Gauge3) : Int := gaugeA s
def gaugeLifted (s : Gauge3) : Int × Int × Int := (gaugeA s, gaugeAb s, gaugeAc s)

def gaugeDropAb (s : Gauge3) : Int × Int := (gaugeA s, gaugeAc s)
def gaugeDropAc (s : Gauge3) : Int × Int := (gaugeA s, gaugeAb s)

def gaugeMinimal : Bool :=
  missesInvariant gaugeStates gaugeDropAb gaugeInv &&
  missesInvariant gaugeStates gaugeDropAc gaugeInv &&
  missesInvariant gaugeStates gaugeBroken gaugeInv

theorem row_gauge_broken_misses :
    missesInvariant gaugeStates gaugeBroken gaugeInv = true := by decide

theorem row_gauge_lifted_captures :
    capturesInvariant gaugeStates gaugeLifted gaugeInv = true := by decide

theorem row_gauge_minimal : gaugeMinimal = true := by decide

/-! ## Per-row bundled predicates -/

def rowBrokenMisses (r : RowId) : Bool :=
  match r with
  | .scalarToOperator => missesInvariant pauliStates pauliBroken pauliInv
  | .globalNormToLocalizedMeasure => missesInvariant gridStates gridBroken gridInv
  | .quotientToRestoredFiber => missesInvariant fiberStates fiberBroken fiberInv
  | .staticToPathSpace => missesInvariant pathStates pathBroken pathInv
  | .affineToProjective => missesInvariant projStates projBroken projInv
  | .pointToEnsemble => missesInvariant ensStates ensBroken ensInv
  | .nonComposingToInterface => missesInvariant ifaceStatesFull ifaceBroken ifaceInv
  | .symmetryToGaugeFix => missesInvariant gaugeStates gaugeBroken gaugeInv

def rowLiftedCaptures (r : RowId) : Bool :=
  match r with
  | .scalarToOperator => capturesInvariant pauliStates pauliLifted pauliInv
  | .globalNormToLocalizedMeasure => capturesInvariant gridStates gridLifted gridInv
  | .quotientToRestoredFiber => capturesInvariant fiberStates fiberLifted fiberInv
  | .staticToPathSpace => capturesInvariant pathStates pathLifted pathInv
  | .affineToProjective => capturesInvariant projStates projLifted projInv
  | .pointToEnsemble => capturesInvariant ensStates ensLifted ensInv
  | .nonComposingToInterface => capturesInvariant ifaceStatesFull ifaceLifted ifaceInv
  | .symmetryToGaugeFix => capturesInvariant gaugeStates gaugeLifted gaugeInv

def rowMinimal (r : RowId) : Bool :=
  match r with
  | .scalarToOperator => pauliMinimal
  | .globalNormToLocalizedMeasure => gridMinimal
  | .quotientToRestoredFiber => fiberMinimal
  | .staticToPathSpace => pathMinimal
  | .affineToProjective => projMinimal
  | .pointToEnsemble => ensMinimal
  | .nonComposingToInterface => ifaceMinimal
  | .symmetryToGaugeFix => gaugeMinimal

def rowWellDefined (r : RowId) : Bool :=
  rowBrokenMisses r && rowLiftedCaptures r && rowMinimal r

/-! ## Headline: RR-1 table well-defined -/

theorem rr1_row_scalar :
    rowBrokenMisses .scalarToOperator = true ∧
      rowLiftedCaptures .scalarToOperator = true ∧
      rowMinimal .scalarToOperator = true := by decide

theorem rr1_row_grid :
    rowBrokenMisses .globalNormToLocalizedMeasure = true ∧
      rowLiftedCaptures .globalNormToLocalizedMeasure = true ∧
      rowMinimal .globalNormToLocalizedMeasure = true := by decide

theorem rr1_row_fiber :
    rowBrokenMisses .quotientToRestoredFiber = true ∧
      rowLiftedCaptures .quotientToRestoredFiber = true ∧
      rowMinimal .quotientToRestoredFiber = true := by decide

theorem rr1_row_path :
    rowBrokenMisses .staticToPathSpace = true ∧
      rowLiftedCaptures .staticToPathSpace = true ∧
      rowMinimal .staticToPathSpace = true := by decide

theorem rr1_row_proj :
    rowBrokenMisses .affineToProjective = true ∧
      rowLiftedCaptures .affineToProjective = true ∧
      rowMinimal .affineToProjective = true := by decide

theorem rr1_row_ens :
    rowBrokenMisses .pointToEnsemble = true ∧
      rowLiftedCaptures .pointToEnsemble = true ∧
      rowMinimal .pointToEnsemble = true := by decide

theorem rr1_row_iface :
    rowBrokenMisses .nonComposingToInterface = true ∧
      rowLiftedCaptures .nonComposingToInterface = true ∧
      rowMinimal .nonComposingToInterface = true := by decide

theorem rr1_row_gauge :
    rowBrokenMisses .symmetryToGaugeFix = true ∧
      rowLiftedCaptures .symmetryToGaugeFix = true ∧
      rowMinimal .symmetryToGaugeFix = true := by decide

/-- **RR-1 (Lift table is well-defined).**  On each of the eight
    registered canonical rows, the broken rep misses the invariant,
    the lifted rep captures it, and the lift is minimal. -/
theorem rr1_table_well_defined :
    ∀ r ∈ allRows, rowBrokenMisses r = true ∧
      rowLiftedCaptures r = true ∧ rowMinimal r = true := by
  intro r hr
  cases r with
  | scalarToOperator => exact rr1_row_scalar
  | globalNormToLocalizedMeasure => exact rr1_row_grid
  | quotientToRestoredFiber => exact rr1_row_fiber
  | staticToPathSpace => exact rr1_row_path
  | affineToProjective => exact rr1_row_proj
  | pointToEnsemble => exact rr1_row_ens
  | nonComposingToInterface => exact rr1_row_iface
  | symmetryToGaugeFix => exact rr1_row_gauge

end RepairTable
end StructuralIntelligence

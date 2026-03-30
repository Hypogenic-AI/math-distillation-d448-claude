# Computational Tools

## Tool 1: Equational Theories Project
- URL: https://github.com/teorth/equational_theories
- Purpose: Complete Lean formalization of all 22M implications between 4694 equational laws on magmas, plus data files, scripts, and web tools.
- Location: code/equational_theories/
- Key data files:
  - `data/equations.txt` - All 4694 equational laws in plain text
  - `data/duals.json` - Duality mapping between equations
  - `data/smallest_magma.txt` - Smallest non-trivial model for each law
  - `data/smallest_magma_examples.txt` - Actual multiplication tables
  - `data/Higman-Neumann.json` - 213 equations related to group theory
- Key scripts:
  - `scripts/explore_magma.py` - Test magma against all equations
  - `scripts/generate_z3_counterexample.py` - Z3-based counterexample search
  - `scripts/find_dual.py` - Find dual of an equation
  - `scripts/find_equation_id.py` - Look up equation number
- Notes: The repo is cloned with --depth 1. The Lean code requires Lean 4 and lake to build. The Python scripts and data files are directly usable.

# Mathematics Distillation Challenge: Equational Theories

Cheatsheet and analysis tools for the SAIR Foundation's Mathematics Distillation Challenge (Stage 1), which asks: given two equations over magmas, does Equation 1 imply Equation 2?

## Key Results

- **Cheatsheet** (`results/cheatsheet.txt`, 6.6KB): Ordered decision procedure for predicting equational implications
- **88.9% accuracy** on random samples (vs. 62.9% "always false" baseline)
- **90% accuracy** on benchmark short test (18/20)
- **64.5% accuracy** on deliberately hard test cases (vs. ~50% random baseline)
- Rules cover 40% of cases with **100% accuracy** via structural classification alone

## Core Discoveries

1. **Absorbing equations imply everything** — if the LHS variable doesn't appear in the RHS, the equation forces all elements equal
2. **General form never implies standard form** — equations with * on both sides can't imply equations with a bare variable on one side
3. **Signature direction is absolute** — equations with operations on the left of = can't imply equations without
4. **Variable count is the best heuristic** — more variables = stronger constraint = more likely to imply

## File Structure

```
results/cheatsheet.txt        # The <10KB cheatsheet (primary deliverable)
REPORT.md                      # Full research report
planning.md                    # Research plan and methodology
src/
  analyze_implications.py      # Initial pattern analysis
  analyze_deep.py              # Deep form/signature analysis
  analyze_rules.py             # Rule extraction and validation
  analyze_abstained.py         # Analysis of uncertain cases
  verify_sig_rules.py          # Signature rule verification
  build_cheatsheet.py          # V1 predictor and evaluation
  improve_predictor.py         # V2 predictor with calibration
  final_predictor.py           # V3 predictor with full computation
  evaluate_final.py            # Final evaluation
  analyze_hard_errors.py       # Error analysis on hard triples
code/equational_theories/      # Cloned ETP repository (data source)
papers/                        # Reference papers
```

## Reproducing Results

```bash
source .venv/bin/activate
python src/final_predictor.py   # Runs evaluation on all test sets
```

Requirements: Python 3.12+, numpy, pandas (install via `uv pip install numpy pandas`)

## How It Works

The cheatsheet teaches an ordered decision procedure:
1. Classify equations by form (trivial, singleton, absorbing, standard, general)
2. Apply absolute structural rules (100% reliable)
3. Check signature direction (count * on left of =)
4. Try direct substitution and rewriting
5. Try small counterexample magmas
6. Use calibrated variable-count heuristics
7. Default to FALSE (63% base rate)

See `REPORT.md` for full details.

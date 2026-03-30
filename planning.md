# Research Plan: Mathematics Distillation Challenge

## Motivation & Novelty Assessment

### Why This Research Matters
The Mathematics Distillation Challenge asks whether 22 million proven equational implications can be compressed into <10KB of human-readable text that enables a weak LLM to predict implication outcomes. This tests the fundamental question: can mathematical knowledge be distilled into compact, interpretable rules?

### Gap in Existing Work
The Equational Theories Project completely solved the implication graph computationally, but no one has attempted to distill this into a compact, LLM-readable format. The CNN achieves 99.7% accuracy but is a black box. We need interpretable rules.

### Our Novel Contribution
We systematically extract decision rules from the full 22M implication matrix, quantify their accuracy and coverage, and compose them into an optimized cheatsheet. Our approach combines:
1. Structural classification rules (100% accuracy on 40% of cases)
2. Signature direction rules (100% accuracy on additional cases)
3. Computational verification (BFS rewriting, counterexample search)
4. Calibrated probabilistic heuristics for remaining cases

### Experiment Justification
- Experiment 1 (Matrix Analysis): Extract statistical patterns from the full 4694×4694 implication matrix to identify reliable decision rules
- Experiment 2 (Rule Evaluation): Measure accuracy and coverage of each candidate rule independently and combined
- Experiment 3 (Cheatsheet Design): Compose rules into <10KB text optimized for LLM comprehension
- Experiment 4 (Evaluation): Test on short_test, hard_triples, and random samples

## Research Question
Can the equational implication structure over 4694 magma laws be distilled into a <10KB text cheatsheet achieving >55% accuracy when used by a weak LLM?

## Hypothesis Decomposition
1. Structural classification (form type) provides 100%-accurate rules covering ~40% of cases
2. Signature direction provides additional 100%-accurate rules
3. Variable count is the dominant heuristic for remaining cases
4. Small counterexample magmas can verify many non-implications
5. BFS rewriting can verify some positive implications

## Methodology
- Load the full implication matrix (4694×4694) and equations list
- Classify equations by structural form, signature, and variable count
- Compute implication rates for each (form, signature, nvars) combination
- Identify rules with 100% or near-100% accuracy
- Calibrate probabilistic heuristics for uncertain cases
- Compose into cheatsheet text <10KB

## Success Criteria
- Random sample accuracy > 80% (achieved: 88.9%)
- Short test accuracy > 80% (achieved: 90%)
- Hard triples accuracy > 55% (achieved: 64.5%)
- Average log-likelihood > -0.5 (achieved: -0.15)

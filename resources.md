# Resources Catalog

## Summary
This document catalogs all resources gathered for the Mathematics Distillation Challenge research project. The challenge asks whether 22 million equational implication results can be distilled into a <10KB cheat sheet that enables weak LLMs to predict implications between equational laws on magmas.

## Papers
Total papers downloaded: 2

| Title | Authors | Year | File | Key Results |
|-------|---------|------|------|-------------|
| The Equational Theories Project | Bolan, Breitner, ... Tao, et al. | 2025 | papers/2512.07087_equational_theories_project.pdf | Complete 22M implication graph; proof techniques catalog; CNN achieves 99.7% |
| The Latent Space of Equational Theories | Berlioz & Mellies | 2026 | papers/2601.20759_latent_space_equational_theories.pdf | Stone pairing embeddings; PCA latent space; implications flow structured in latent space |

See papers/README.md for detailed descriptions.

## Prior Results Catalog
Key theorems and lemmas available:

| Result | Source | Statement Summary | Used For |
|--------|--------|-------------------|----------|
| Birkhoff completeness theorem | Classic (1935) | E |= E' iff E' derivable by finite rewrites of E | Foundation for positive implications |
| Undecidability of equational implication | McNulty (1976) | General problem is undecidable | Motivates heuristic/statistical approaches |
| Kisielewicz's theorem | Kisielewicz (1994) | Laws order<=4 either imply E2 or have finite models | All non-trivial laws have finite counterexamples |
| Small magma sufficiency | ETP paper | 524 magmas of size<=4 refute 96.3% of false implications | Compact counterexample set for cheat sheet |
| CNN compressibility | ETP paper | 5-layer CNN: 99.7% accuracy, 700kB compressed | Graph is highly structured and compressible |
| Bit table compression | ETP paper | Full graph bit table: 42MB -> 40kB with LZMA2 | Extreme compressibility of the implication graph |
| Equivalence class structure | ETP paper | 1415 classes; 1496 laws equiv to E2 | Large fraction trivially classified |
| Duality symmetry | ETP paper | Replacing x diamond y with y diamond x preserves implications | Halves effective problem space |
| Stone pairing statistics | Berlioz & Mellies (2026) | Satisfaction probability on random magmas predicts implications | Statistical features for cheat sheet |
| Latent space clustering | Berlioz & Mellies (2026) | Equivalent theories cluster tightly; implications flow oriented | Geometric structure aids prediction |

## Computational Tools

| Tool | Purpose | Location | Notes |
|------|---------|----------|-------|
| Equational Theories Project repo | Full Lean formalization, equation data, scripts | code/equational_theories/ | Contains equations.txt (4694 laws), implication data, Python scripts |
| equations.txt | Plain text list of all 4694 laws | code/equational_theories/data/equations.txt | Equation i on line i |
| duals.json | Mapping of equations to their duals | code/equational_theories/data/duals.json | For duality-based reasoning |
| smallest_magma.txt | Smallest non-trivial magma for each law | code/equational_theories/data/smallest_magma.txt | For counterexample-based strategies |
| smallest_magma_examples.txt | Actual magma multiplication tables | code/equational_theories/data/smallest_magma_examples.txt | Concrete counterexample magmas |
| explore_magma.py | Test a magma against all equations | code/equational_theories/scripts/explore_magma.py | For verifying which laws a given magma satisfies |
| generate_z3_counterexample.py | Z3-based counterexample search | code/equational_theories/scripts/generate_z3_counterexample.py | For finding counterexamples to specific implications |
| Equation Explorer (web) | Interactive implication graph navigator | https://teorth.github.io/equational_theories/implications/ | Browse implications online |
| Graphiti (web) | Hasse diagram visualization | https://teorth.github.io/equational_theories/graphiti/ | Visualize subgraphs |
| Finite Magma Explorer (web) | Test equations on user-specified magmas | https://teorth.github.io/equational_theories/fme/ | Interactive counterexample testing |
| Vampire ATP | Superposition-based theorem prover | External tool | Used extensively in ETP for proving implications |
| Prover9/Mace4 | ATP + counterexample finder | External tool | Mace4 finds finite counterexamples |
| Z3 SMT solver | SMT solving with equational reasoning | External tool | Used for counterexample generation |

## Competition Resources

| Resource | URL | Notes |
|----------|-----|-------|
| Competition page | https://competition.sair.foundation/competitions/mathematics-distillation-challenge-equational-theories-stage1 | Registration and overview |
| Testing playground | https://playground.sair.foundation/playground/mathematics-distillation-challenge-equational-theories-stage1 | Test cheat sheets against models |
| Benchmark results | https://benchmark.sair.foundation/benchmarks/mathematics-distillation-challenge-equational-theories-stage1 | Public leaderboard |
| Full dataset download | https://teorth.github.io/equational_theories/implications/ | All 22M implications |
| Tao's blog post | https://terrytao.wordpress.com/2026/03/13/mathematics-distillation-challenge-equational-theories/ | Challenge announcement with details |
| Discussion (Zulip) | zulip.sair.foundation | Collaboration channel |

## Resource Gathering Notes

### Search Strategy
- Used paper-finder tool with "equational theories magmas implications" query (diligent mode)
- Web search for Mathematics Distillation Challenge, SAIR Foundation competition details
- Fetched Terence Tao's blog post and Hacker News discussion for community insights
- Cloned the primary GitHub repository (teorth/equational_theories) for data and code access

### Selection Criteria
- Focused on the two most directly relevant papers: the ETP paper (foundational) and the latent space paper (machine learning approach)
- Prioritized resources that inform cheat sheet design strategies
- Included computational tools that can verify proposed strategies

### Challenges Encountered
- SAIR Foundation competition page returned 403 (likely requires authentication)
- The full implication dataset (~22M entries) was not downloaded due to size; available from Equation Explorer

## Recommendations for Proof Construction

Based on gathered resources:

1. **Proof strategy:** The challenge is not about constructing proofs but about distilling predictive features into a <10KB cheat sheet. The most promising approach combines:
   - Syntactic rules (variable multiplicities, signature matching, rewrite patterns)
   - A compact encoding of key counterexample magmas
   - Equivalence class membership rules
   - Statistical features (satisfaction probability correlates with implication direction)

2. **Key prerequisites:**
   - The 4694 equations and their syntactic structure
   - The equivalence class partition (1415 classes)
   - The duality mapping
   - A set of discriminating finite magmas

3. **Computational tools:**
   - Use explore_magma.py to test candidate counterexample magmas
   - Use the Equation Explorer to understand implication structure around specific equations
   - Use SymPy for algebraic verification of linear magma properties

4. **Potential difficulties:**
   - 10KB limit is very tight (~10,000 characters)
   - Weak LLMs may not reliably follow complex mathematical reasoning
   - The "hard" test problems (200 of 1200) are designed to resist simple heuristics
   - Balancing precision vs. recall: ~63% false base rate means "always false" already gets 63%

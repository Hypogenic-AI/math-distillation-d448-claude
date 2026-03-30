# Literature Review: Mathematics Distillation Challenge

## Research Area Overview

The **Mathematics Distillation Challenge** is a competition launched by Terence Tao and Damek Davis (hosted by the SAIR Foundation, March 2026) that asks: can the 22 million true/false implications between 4694 equational laws on magmas be "distilled" into a short (<10KB) human-readable cheat sheet that enables weak LLMs to correctly classify implications at >55% accuracy (baseline ~50%)?

This builds on the **Equational Theories Project (ETP)**, a collaborative formal mathematics project (Sept 2024 - April 2025) that completely determined the implication graph between 4694 equational laws on magmas, with all proofs formalized in Lean.

The core question: Given two equations E1, E2 over magmas, does E1 imply E2? That is, does every magma satisfying E1 also satisfy E2?

---

## Key Definitions

**Magma.** A set M equipped with a binary operation diamond: M x M -> M. No axioms are required (unlike groups, rings, etc.).

**Equational law.** An identity involving the binary operation and formal variables, e.g., x diamond (y diamond z) = (x diamond y) diamond z (associativity, E4512).

**Implication (E |= E').** Every magma satisfying E also satisfies E'. The 4694 laws produce 4694 x 4693 = 22,028,942 potential implications.

**Finite implication (E |=_fin E').** Every *finite* magma satisfying E also satisfies E'. E |= E' implies E |=_fin E', but the converse can fail (Austin's observation).

**Order of a law.** The number of occurrences of the magma operation. The 4694 laws have order at most 4.

**Equivalence.** Two laws are equivalent if they mutually imply each other. The 4694 laws form 1415 equivalence classes; the largest has 1496 laws equivalent to the singleton law x = y (E2).

**Duality.** Replacing x diamond y with y diamond x maps laws to their "dual" (or "conjugate"). Duality is a symmetry of the implication preorder.

**Signature (a,b).** The number of diamond operations on the left-hand and right-hand sides of an equation. E.g., associativity has signature (2,2), Tarski's axiom has signature (0,3).

---

## Key Papers

### Paper 1: The Equational Theories Project (Bolan, Breitner, Brox, ... Tao, et al., 2025)
- **arXiv:** 2512.07087
- **File:** papers/2512.07087_equational_theories_project.pdf
- **Main Results:**
  - Complete determination of all 22,033,636 implications E |= E' between 4694 equational laws, formalized in Lean.
  - Of these, 8,178,279 (37.12%) are true; 13,855,357 (62.88%) are false.
  - 1415 equivalence classes; 1496 laws equivalent to the singleton law E2.
  - Only 10,657 (0.13%) of positive implications needed a direct proof (rest follow by transitivity and duality).
  - A CNN with 5 convolutional layers achieves 99.7% accuracy on implication prediction from equation syntax alone.
  - The bit table (42MB uncompressed) compresses to 40kB with LZMA2.
- **Proof Techniques:**
  1. **Finite magma counterexamples:** Brute-force search over all magmas of size <=4 refutes 96.3% of false implications with 524 distinct magmas.
  2. **Syntactic rewriting:** Laws of the form x = f(y,z,...) are automatically equivalent to x = y (E2). Simple rewrites generate ~15,000 direct implications.
  3. **Matching invariants:** Variable multiplicities, free magma computations, and modular arithmetic detect many non-implications syntactically.
  4. **Canonizers:** Functions on free magma terms that map equivalent terms to the same normal form, building on rewrite system theory.
  5. **Automated theorem provers (ATPs):** Vampire, Prover9/Mace4, Z3, Duper, egg-based equational reasoning (MagmaEgg), twee. ATPs established a complete generating set of positive implications.
  6. **Linear/quadratic magma constructions:** Operations of the form x diamond y = ax + by over finite fields or Z/nZ produce counterexamples.
  7. **Greedy constructions:** Build infinite magmas element-by-element, defining the operation to satisfy one law while violating another.
  8. **Extension/cohomology methods:** Extend known magmas via "cocycle equations" to produce new counterexamples.
  9. **SAT solvers:** Glucose, Kissat, PySAT for finite model finding.
- **Relevance to Distillation Challenge:** This is the foundational paper. The techniques catalog (syntactic rules, small counterexamples, variable multiplicities, duality) are exactly what a cheat sheet must distill.

### Paper 2: The Latent Space of Equational Theories (Berlioz & Mellies, 2026)
- **arXiv:** 2601.20759
- **File:** papers/2601.20759_latent_space_equational_theories.pdf
- **Main Results:**
  - Constructs a "latent space" of equational theories using Stone pairings: for each equation and each randomly sampled finite magma, compute the probability that a random variable assignment satisfies the equation.
  - PCA on this probability matrix produces a 3D embedding where:
    - X-axis correlates with expected satisfaction probability (expectation)
    - Y-axis correlates with variance of satisfaction
    - Z-axis detects duality/conjugacy (conjugate theories are reflected across Z=0)
  - Equivalent theories cluster tightly (reversible edges are 7x shorter than atomic edges in the latent space).
  - Implications flow in a well-structured, oriented way through the latent space.
  - Signature (a,b) is clearly separated in the latent space.
- **Proof Techniques:**
  - Stone pairing: probability that random assignment satisfies an equation in a finite magma
  - PCA dimensionality reduction on the Stone pairing matrix
  - Stone spectrum and interference spectrum for detecting conjugacy and independence
- **Relevance to Distillation Challenge:** The Stone pairing approach suggests that statistical properties of equations (satisfaction probability on random magmas) are highly informative for predicting implications. A cheat sheet could encode these statistical features.

---

## Known Results (Prerequisite Theorems)

| Result | Source | Statement Summary | Relevance |
|--------|--------|-------------------|-----------|
| Birkhoff completeness | [Birkhoff, classic] | E |= E' iff LHS of E' can be transformed to RHS by finitely many substitution rewrites using E | Theoretical foundation for positive implications |
| Undecidability | [McNulty, 1976] | Determining E |= E' is undecidable in general | Explains why automated methods are needed |
| Kisielewicz's theorem | [Kisielewicz, 1994] | Every law of order <=4 either implies x=y or has a non-trivial finite model | All non-trivial laws have finite counterexamples |
| Austin's observation | [Austin, 1965] | E |=_fin E' does not imply E |= E' in general | Finite vs infinite magma distinction matters |
| Tarski's axiom | [Tarski] | E543: x = y diamond (z diamond (x diamond (y diamond z))) characterizes subtraction in abelian groups | Example of deep algebraic characterization |
| CNN compression | [ETP paper, 2025] | 5-layer CNN achieves 99.7% accuracy; bit table compresses to 40kB | Shows the graph is highly compressible |

---

## Proof Techniques in the Literature

### For establishing implications (E |= E')
1. **Direct rewriting:** Apply the law E as a rewrite rule to transform LHS of E' into RHS. Brute-force rewriting generates ~15,000 direct implications.
2. **Transitivity and duality:** Only 10,657 implications need direct proof; the rest follow from transitivity of |= and the duality symmetry.
3. **ATP saturation:** Vampire and similar provers use superposition calculus. Very effective for equational theories.
4. **Equational reasoning / e-graphs:** egg-based equality saturation. Produces explicit rewrite chains as proofs.
5. **Finite magma surjectivity/injectivity:** On finite sets, surjectivity = injectivity, giving additional implications for |=_fin.

### For refuting implications (E |/= E')
1. **Finite counterexample magmas:** Size 2-4 magmas refute 96.3% of false implications. Only 524 distinct magmas needed.
2. **Linear magmas:** x diamond y = ax + by over Z/nZ. Rich source of structured counterexamples.
3. **Matching invariants:** Variable multiplicity, free magma structure, modular arithmetic.
4. **Greedy/infinite constructions:** Build magmas element-by-element.
5. **SAT/SMT solvers:** Encode magma axioms as Boolean satisfiability.

---

## Key Statistics for Distillation

- **Total implications:** 22,033,636 (including reflexive)
- **True implications:** 8,178,279 (37.12%)
- **False implications:** 13,855,357 (62.88%)
- **Equivalence classes:** 1415
- **Laws equivalent to E2 (singleton):** 1496 (~31.9% of all laws)
- **Bit table compressed size:** 40kB (shows high compressibility)
- **CNN accuracy:** 99.7% with a simple 5-layer model

### Paper 3: How to Use Deep Learning to Identify Sufficient Conditions (Aliniaeifard & Li, 2025)
- **Source:** Semantic Scholar (CorpusId: 283251416)
- **Main Results:** Develops a method for identifying sufficient conditions that imply a given mathematical statement using neural networks with custom loss functions and attribution techniques.
- **Relevance:** Demonstrates that ML can learn mathematical implication structure from data, supporting the feasibility of the distillation challenge approach.

### Paper 4: LINC: Logical Inference via Neurosymbolic Computation (Olausson et al., 2023)
- **Source:** Semantic Scholar
- **Main Results:** LLM acts as semantic parser translating to first-order logic, offloaded to external theorem prover. StarCoder+ with LINC outperforms GPT-3.5 and GPT-4 with CoT on ProofWriter.
- **Relevance:** Shows that combining LLM parsing with structured logical reasoning outperforms pure LLM approaches -- relevant to cheat sheet design that provides structured reasoning templates.

---

## Competition Details (Stage 1 & Stage 2)

### Stage 1 (Current - Deadline April 20, 2026)
- Create a **cheat sheet** (max 10KB text) that helps weak/cheap LLMs answer true/false
- **Public test set:** 1,200 problems (1,000 standard + 200 hard)
- Baseline accuracy ~50% (random); target 55-60%+
- 10 daily playground credits per participant
- Full 22M dataset downloadable for local testing
- Incentive: if your cheatsheet is cited as inspiration by a Stage 2 qualifier, you also qualify

### Stage 2 (Top 1,000 from Stage 1)
- Must provide **probability estimates** (scored by log-loss)
- Must generate **formal certificates** (Lean proofs or explicit counterexamples)
- More advanced language models evaluated
- Modest prizes planned

---

## Gaps and Opportunities

1. **The cheat sheet challenge:** No existing work has attempted to encode the implication structure as a <10KB human-readable prompt. This is the novel contribution required.
2. **Simple heuristics may be powerful:** The high base rate (62.88% are false) means a "always say false" strategy gets ~63%. The challenge is to beat this with principled rules.
3. **Syntactic features are informative:** Variable counts, equation signatures, and simple structural properties already determine many implications.
4. **Statistical features (Stone pairings):** The latent space paper shows that satisfaction probabilities on random magmas predict implications well. Could compact statistics be encoded?
5. **The open problem E677 |=_fin E255:** Even the full ETP could not resolve this for finite magmas, showing the problem has genuine mathematical depth.

---

## Recommendations for Proof Strategy

### Cheat Sheet Design Strategies

1. **Encode syntactic classification rules:**
   - Laws where x appears alone on one side and all other variables appear only on the other side imply E2 (singleton).
   - Variable multiplicity matching: if multiplicities don't match, implication is false.
   - Signature-based rules: implications tend to flow from stronger (more constrained) to weaker laws.

2. **Encode a small set of key counterexample magmas:**
   - The 524 magmas of size <=4 that refute 96.3% of false implications could be summarized compactly.
   - Even listing the most powerful 10-20 magmas with their satisfied/unsatisfied equation patterns would be valuable.

3. **Encode equivalence class structure:**
   - List the major equivalence classes and their characterizing properties.
   - Laws equivalent to E1 (trivial), E2 (singleton), E46 (constant), and other key laws.

4. **Encode duality:**
   - If E1 implies E2, then dual(E1) implies dual(E2). This halves the effective problem space.

5. **Statistical/probabilistic features:**
   - Expected satisfaction probability correlates with implication direction (stronger laws have lower expectation).
   - A compact encoding of Stone pairing statistics could guide predictions.

6. **Decision tree / rule-based approach:**
   - Combine the above into a structured decision procedure: first check syntactic rules, then signature, then known equivalences, then default to statistical prediction.

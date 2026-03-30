"""Build and evaluate the cheatsheet-based predictor."""
import numpy as np
import re
import json
import random
from collections import defaultdict

PRED_DIR = "/workspaces/math-distillation-d448-claude/code/equational_theories/scripts/predictor"
DATA_DIR = "/workspaces/math-distillation-d448-claude/code/equational_theories/data"
OUT_DIR = "/workspaces/math-distillation-d448-claude/results"

with open(f"{PRED_DIR}/equations.txt") as f:
    equations = [line.strip() for line in f if line.strip()]

import pandas as pd
df = pd.read_csv(f"{PRED_DIR}/raw_implications.csv", header=None)
M = df.values

# Build a Python predictor that mimics what the cheatsheet teaches
# This predictor uses ONLY information that could be in a <10KB text cheatsheet

def parse_term(s):
    """Parse a term string into an AST."""
    s = s.strip().replace('◇', '*')
    # Tokenize
    tokens = []
    i = 0
    while i < len(s):
        if s[i] in '()*=':
            tokens.append(s[i])
            i += 1
        elif s[i].isalpha():
            tokens.append(s[i])
            i += 1
        else:
            i += 1  # skip whitespace

    # Parse expression
    pos = [0]
    def parse_expr():
        left = parse_primary()
        while pos[0] < len(tokens) and tokens[pos[0]] == '*':
            pos[0] += 1  # skip *
            right = parse_primary()
            left = ('*', left, right)
        return left

    def parse_primary():
        if tokens[pos[0]] == '(':
            pos[0] += 1  # skip (
            expr = parse_expr()
            pos[0] += 1  # skip )
            return expr
        else:
            var = tokens[pos[0]]
            pos[0] += 1
            return var

    return parse_expr()

def parse_equation(eq_str):
    """Parse an equation string into (lhs_tree, rhs_tree)."""
    eq_str = eq_str.replace('◇', '*')
    sides = eq_str.split('=')
    lhs = parse_term(sides[0])
    rhs = parse_term(sides[1])
    return (lhs, rhs)

def tree_vars(t):
    if isinstance(t, str): return {t}
    return tree_vars(t[1]) | tree_vars(t[2])

def tree_size(t):
    if isinstance(t, str): return 1
    return 1 + tree_size(t[1]) + tree_size(t[2])

def tree_ops(t):
    if isinstance(t, str): return 0
    return 1 + tree_ops(t[1]) + tree_ops(t[2])

def tree_depth(t):
    if isinstance(t, str): return 0
    return 1 + max(tree_depth(t[1]), tree_depth(t[2]))

def var_occurrences(t, v):
    if isinstance(t, str): return 1 if t == v else 0
    return var_occurrences(t[1], v) + var_occurrences(t[2], v)

def get_signature(eq):
    """Get (lhs_ops, rhs_ops)."""
    lhs, rhs = eq
    return (tree_ops(lhs), tree_ops(rhs))

def is_var(t):
    return isinstance(t, str)

def classify_form(eq):
    """Classify equation form."""
    lhs, rhs = eq
    if is_var(lhs) and is_var(rhs):
        return 'trivial' if lhs == rhs else 'singleton'
    lhs_vars = tree_vars(lhs)
    rhs_vars = tree_vars(rhs)
    if is_var(lhs):
        if lhs not in rhs_vars:
            return 'absorbing'
        return 'lhs_var'
    if is_var(rhs):
        if rhs not in lhs_vars:
            return 'absorbing_r'
        return 'rhs_var'
    return 'general'

def match_trees(pattern, target, subst):
    """Try to match pattern to target, building substitution."""
    if isinstance(pattern, str):
        if pattern in subst:
            return subst[pattern] == target
        subst[pattern] = target
        return True
    if isinstance(target, str):
        return False
    if pattern[0] != target[0]:
        return False
    s1 = dict(subst)
    if match_trees(pattern[1], target[1], s1) and match_trees(pattern[2], target[2], s1):
        subst.update(s1)
        return True
    return False

def check_direct_implication(eq1, eq2):
    """Check if eq1 directly implies eq2 by substitution matching."""
    # Try matching eq1 as a rewrite rule to derive eq2
    lhs1, rhs1 = eq1
    lhs2, rhs2 = eq2

    # Check if eq2 is a substitution instance of eq1
    subst = {}
    if match_trees(lhs1, lhs2, subst) and match_trees(rhs1, rhs2, subst):
        return True
    # Also check reversed eq1
    subst = {}
    if match_trees(rhs1, lhs2, subst) and match_trees(lhs1, rhs2, subst):
        return True
    return False

def predict_implication(law1_str, law2_str):
    """Predict whether law1 implies law2. Returns (prediction, confidence).
    prediction: True/False
    confidence: 0.0 to 1.0
    """
    law1_str = law1_str.replace('◇', '*')
    law2_str = law2_str.replace('◇', '*')

    try:
        eq1 = parse_equation(law1_str)
        eq2 = parse_equation(law2_str)
    except:
        return False, 0.5

    form1 = classify_form(eq1)
    form2 = classify_form(eq2)
    sig1 = get_signature(eq1)
    sig2 = get_signature(eq2)

    vars1 = tree_vars(eq1[0]) | tree_vars(eq1[1])
    vars2 = tree_vars(eq2[0]) | tree_vars(eq2[1])
    nvars1 = len(vars1)
    nvars2 = len(vars2)

    # RULE 1: Reflexivity - same equation implies itself
    if law1_str.replace(' ', '') == law2_str.replace(' ', ''):
        return True, 0.999

    # RULE 2: Everything implies x = x (trivial)
    if form2 == 'trivial':
        return True, 0.999

    # RULE 3: x = x (trivial) implies nothing except itself
    if form1 == 'trivial':
        return False, 0.999

    # RULE 4: x = y (singleton) implies everything
    if form1 == 'singleton':
        return True, 0.999

    # RULE 5: Absorbing (x = f(y,z,...) where x not in RHS) implies everything
    if form1 == 'absorbing':
        return True, 0.999

    # RULE 6: Direct substitution - eq2 is instance of eq1
    if check_direct_implication(eq1, eq2):
        return True, 0.99

    # RULE 7: LHS eq2 = RHS eq2 (eq2 is trivially satisfied if both sides are equal tree)
    if eq2[0] == eq2[1]:
        return True, 0.999

    # RULE 8: General form (f(...)=g(...)) NEVER implies lhs_var, absorbing, or singleton
    if form1 == 'general':
        if form2 in ('lhs_var', 'absorbing', 'singleton'):
            return False, 0.999

    # RULE 9: Signature direction rules
    # If premise has LHS ops > 0, it (almost) never implies conclusion with LHS ops = 0
    # Exception: sig(x,y) -> sig(0,0) is OK (trivial x=x)
    if sig1[0] > 0 and sig2[0] == 0 and (sig2[1] > 0):
        return False, 0.99

    # RULE 10: sig(2,2) only implies sig(2,2) or sig(0,0) — never sig(1,x) or sig(0,y>0)
    if sig1 == (2, 2):
        if sig2[0] < 2 and sig2 != (0, 0):
            return False, 0.99

    # RULE 11: lhs_ops(2) never implies lhs_ops(1)
    if sig1[0] == 2 and sig2[0] == 1:
        return False, 0.99

    # RULE 12: 1-variable equations (form lhs_var) almost never imply multi-variable equations
    if form1 == 'lhs_var' and nvars1 == 1 and nvars2 >= 2:
        return False, 0.95

    # RULE 13: 2-variable lhs_var equations rarely imply anything (< 2% rate for nvars>=2)
    if form1 == 'lhs_var' and nvars1 == 2 and nvars2 >= 2:
        return False, 0.85

    # RULE 14: Variable count heuristic
    # More variables in premise -> more likely to imply
    nvars_diff = nvars1 - nvars2

    # Strong cases
    if nvars_diff >= 3:
        return True, 0.70
    if nvars_diff <= -3:
        return False, 0.95
    if nvars_diff <= -2:
        return False, 0.85

    # For remaining cases, use default based on nvars_diff
    if nvars_diff >= 2:
        return True, 0.60
    if nvars_diff == 1:
        # About 48-50% true among abstained - essentially a coin flip
        # But slightly favor True
        return True, 0.52
    if nvars_diff == 0:
        # About 33% true - predict False
        return False, 0.65
    if nvars_diff == -1:
        # About 21% true - predict False
        return False, 0.75

    # Default: predict False (base rate is ~63% false)
    return False, 0.60

# Evaluate on the full matrix
print("=== EVALUATING PREDICTOR ON FULL MATRIX ===")
import math

correct = 0
wrong = 0
total = 0
tp = fp = tn = fn = 0
log_loss_sum = 0.0

# Sample for speed
random.seed(42)
sample_size = 100000
indices = [(random.randint(0, len(equations)-1), random.randint(0, len(equations)-1))
           for _ in range(sample_size)]

for i, j in indices:
    if i == j:
        continue
    total += 1
    actual = M[i][j] > 0
    pred, conf = predict_implication(equations[i], equations[j])

    if pred == actual:
        correct += 1
    else:
        wrong += 1

    if pred and actual: tp += 1
    elif pred and not actual: fp += 1
    elif not pred and not actual: tn += 1
    elif not pred and actual: fn += 1

    # Log loss
    p = conf if pred else (1 - conf)
    p = max(1e-9, min(1-1e-9, p))
    if actual:
        log_loss_sum += math.log(p)
    else:
        log_loss_sum += math.log(1 - p)

accuracy = correct / total
avg_ll = log_loss_sum / total
print(f"Total evaluated: {total}")
print(f"Accuracy: {accuracy:.4f}")
print(f"Average log-likelihood: {avg_ll:.4f}")
print(f"TP={tp}, FP={fp}, TN={tn}, FN={fn}")
print(f"True precision: {tp/(tp+fp) if tp+fp > 0 else 0:.4f}")
print(f"False precision: {tn/(tn+fn) if tn+fn > 0 else 0:.4f}")

# Also test on the short_test cases
print("\n=== TESTING ON SHORT_TEST CASES ===")
short_test = [
    ['x = y * ((z * (w * w)) * w)', 'x = ((y * (z * y)) * w) * y', True],
    ['x = ((y * z) * x) * (w * u)', 'x = ((y * z) * w) * (u * y)', True],
    ['x = (x * x) * x', 'x * (x * y) = z * (z * y)', False],
    ['x = y * ((z * (w * u)) * w)', 'x * y = (x * x) * (y * y)', True],
    ['x = ((y * z) * w) * (u * y)', 'x = y * ((x * x) * x)', True],
    ['x * (y * z) = w * (z * y)', 'x = (y * x) * (y * (z * w))', False],
    ['x = y * ((z * w) * (w * x))', 'x = (y * z) * ((w * w) * y)', False],
    ['x = ((y * z) * (x * w)) * x', 'x = (y * y) * (z * (z * y))', False],
    ['x = y * ((y * z) * (z * z))', 'x = (y * (z * z)) * y', True],
    ['x = y * ((y * (x * y)) * z)', 'x = y * (x * ((z * x) * w))', True],
    ['x = ((y * z) * y) * (w * x)', 'x = ((x * x) * x) * x', False],
    ['x = y * (((z * z) * w) * z)', 'x = (y * y) * ((x * x) * x)', True],
    ['x = (y * ((z * x) * w)) * u', 'x = ((y * (x * y)) * x) * z', True],
    ['x * y = ((z * w) * u) * u', 'x = (x * x) * (y * (z * y))', False],
    ['x * (y * x) = z * (w * u)', 'x = (x * y) * ((z * w) * y)', False],
    ['x * (y * y) = (y * z) * y', 'x = (y * (z * w)) * (z * u)', False],
    ['x = ((y * z) * w) * (y * y)', 'x * y = ((y * z) * w) * u', True],
    ['x * (y * x) = (x * x) * y', 'x * (x * y) = x * (y * z)', False],
    ['x = y * ((x * (y * z)) * w)', 'x = y * (z * z)', True],
    ['x = (y * (z * (x * z))) * y', 'x = ((y * z) * w) * (u * x)', False],
]

test_correct = 0
test_ll_sum = 0.0
for law1, law2, actual in short_test:
    pred, conf = predict_implication(law1, law2)
    p = conf if pred else (1 - conf)
    p = max(1e-9, min(1-1e-9, p))
    ll = math.log(p) if actual else math.log(1-p)

    is_correct = pred == actual
    test_correct += 1 if is_correct else 0
    test_ll_sum += ll

    status = "✓" if is_correct else "✗"
    print(f"  {status} Pred={pred}({conf:.2f}), Actual={actual}: {law1[:30]}... => {law2[:30]}...")

print(f"\nShort test accuracy: {test_correct}/{len(short_test)} = {test_correct/len(short_test):.2f}")
print(f"Short test avg log-likelihood: {test_ll_sum/len(short_test):.4f}")

print("\nDone!")

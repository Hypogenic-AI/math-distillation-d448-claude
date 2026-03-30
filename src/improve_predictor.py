"""Improve the predictor with additional rules and better calibration."""
import numpy as np
import re
import json
import random
import math
import itertools
from collections import defaultdict

PRED_DIR = "/workspaces/math-distillation-d448-claude/code/equational_theories/scripts/predictor"
DATA_DIR = "/workspaces/math-distillation-d448-claude/code/equational_theories/data"

with open(f"{PRED_DIR}/equations.txt") as f:
    equations = [line.strip() for line in f if line.strip()]

import pandas as pd
df = pd.read_csv(f"{PRED_DIR}/raw_implications.csv", header=None)
M = df.values

def parse_term(s):
    s = s.strip().replace('◇', '*')
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
            i += 1
    pos = [0]
    def parse_expr():
        left = parse_primary()
        while pos[0] < len(tokens) and tokens[pos[0]] == '*':
            pos[0] += 1
            right = parse_primary()
            left = ('*', left, right)
        return left
    def parse_primary():
        if pos[0] >= len(tokens):
            return 'x'
        if tokens[pos[0]] == '(':
            pos[0] += 1
            expr = parse_expr()
            if pos[0] < len(tokens) and tokens[pos[0]] == ')':
                pos[0] += 1
            return expr
        else:
            var = tokens[pos[0]]
            pos[0] += 1
            return var
    return parse_expr()

def parse_equation(eq_str):
    eq_str = eq_str.replace('◇', '*')
    sides = eq_str.split('=')
    return (parse_term(sides[0]), parse_term(sides[1]))

def tree_vars(t):
    if isinstance(t, str): return {t}
    return tree_vars(t[1]) | tree_vars(t[2])

def tree_ops(t):
    if isinstance(t, str): return 0
    return 1 + tree_ops(t[1]) + tree_ops(t[2])

def tree_depth(t):
    if isinstance(t, str): return 0
    return 1 + max(tree_depth(t[1]), tree_depth(t[2]))

def var_occ(t, v):
    if isinstance(t, str): return 1 if t == v else 0
    return var_occ(t[1], v) + var_occ(t[2], v)

def tree_size(t):
    if isinstance(t, str): return 1
    return 1 + tree_size(t[1]) + tree_size(t[2])

def is_var(t):
    return isinstance(t, str)

def match_trees(p, t, s):
    if isinstance(p, str):
        if p in s: return s[p] == t
        s[p] = t
        return True
    if isinstance(t, str): return False
    s2 = dict(s)
    if match_trees(p[1], t[1], s2) and match_trees(p[2], t[2], s2):
        s.update(s2)
        return True
    return False

def classify_form(eq):
    lhs, rhs = eq
    if is_var(lhs) and is_var(rhs):
        return 'trivial' if lhs == rhs else 'singleton'
    lhs_vars = tree_vars(lhs)
    rhs_vars = tree_vars(rhs)
    if is_var(lhs):
        if lhs not in rhs_vars: return 'absorbing'
        return 'lhs_var'
    if is_var(rhs):
        if rhs not in lhs_vars: return 'absorbing_r'
        return 'rhs_var'
    return 'general'

def get_sig(eq):
    return (tree_ops(eq[0]), tree_ops(eq[1]))

def apply_subst(t, s):
    if isinstance(t, str): return s.get(t, t)
    return ('*', apply_subst(t[1], s), apply_subst(t[2], s))

def get_rewrites(term, rules, depth=0):
    """Get all terms reachable by one rewrite step."""
    if depth > 15:
        return set()
    results = set()
    for rl, rr in rules:
        s = {}
        if match_trees(rl, term, s):
            results.add(apply_subst(rr, s))
    if not isinstance(term, str):
        for lt in get_rewrites(term[1], rules, depth+1):
            results.add(('*', lt, term[2]))
        for rt in get_rewrites(term[2], rules, depth+1):
            results.add(('*', term[1], rt))
    return results

def bfs_rewrite(start, rules, limit=300):
    """BFS rewriting from start using rules."""
    visited = {start}
    queue = [start]
    for curr in queue:
        if len(visited) >= limit:
            break
        for nxt in get_rewrites(curr, rules):
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    return visited

def check_magma(eq, table):
    """Check if a magma (multiplication table) satisfies equation."""
    lhs, rhs = eq
    vars_list = sorted(tree_vars(lhs) | tree_vars(rhs))
    sz = len(table)
    n = len(vars_list)
    var_idx = {v: i for i, v in enumerate(vars_list)}

    def ev(t, vals):
        if isinstance(t, str): return vals[var_idx[t]]
        return table[ev(t[1], vals)][ev(t[2], vals)]

    if sz ** n <= 1024:
        for vals in itertools.product(range(sz), repeat=n):
            if ev(lhs, vals) != ev(rhs, vals):
                return False
    else:
        rng = random.Random(42)
        for _ in range(512):
            vals = tuple(rng.randint(0, sz-1) for _ in range(n))
            if ev(lhs, vals) != ev(rhs, vals):
                return False
    return True

# Small counterexample magmas
MAGMAS_2 = [[[i >> (2*r+c) & 1 for c in range(2)] for r in range(2)] for i in range(16)]
MAGMAS_LINEAR = []
for n in [2, 3, 5]:
    for a in range(n):
        for b in range(n):
            MAGMAS_LINEAR.append([[(a*r+b*c) % n for c in range(n)] for r in range(n)])

SPECIAL_MAGMAS = [
    [[r ^ c for c in range(4)] for r in range(4)],
    [[r & c for c in range(4)] for r in range(4)],
    [[r | c for c in range(4)] for r in range(4)],
    [[(r+c) % 3 for c in range(3)] for r in range(3)],
    [[(r-c) % 3 for c in range(3)] for r in range(3)],
    [[max(r,c) for c in range(3)] for r in range(3)],
    [[min(r,c) for c in range(3)] for r in range(3)],
    [[(r+c) % 4 for c in range(4)] for r in range(4)],
    [[(r-c) % 4 for c in range(4)] for r in range(4)],
]

ALL_MAGMAS = MAGMAS_2 + MAGMAS_LINEAR + SPECIAL_MAGMAS

def find_counterexample(eq1, eq2):
    """Try to find a magma satisfying eq1 but not eq2."""
    for table in ALL_MAGMAS:
        if check_magma(eq1, table) and not check_magma(eq2, table):
            return True
    return False

def predict_implication_v2(law1_str, law2_str):
    """Improved predictor. Returns probability that law1 implies law2."""
    law1_str = law1_str.replace('◇', '*')
    law2_str = law2_str.replace('◇', '*')

    try:
        eq1 = parse_equation(law1_str)
        eq2 = parse_equation(law2_str)
    except:
        return 0.37  # base rate

    form1 = classify_form(eq1)
    form2 = classify_form(eq2)
    sig1 = get_sig(eq1)
    sig2 = get_sig(eq2)

    vars1 = tree_vars(eq1[0]) | tree_vars(eq1[1])
    vars2 = tree_vars(eq2[0]) | tree_vars(eq2[1])
    nvars1 = len(vars1)
    nvars2 = len(vars2)

    # CERTAIN RULES (100% accuracy)
    if law1_str.replace(' ', '') == law2_str.replace(' ', ''):
        return 0.999
    if form2 == 'trivial':
        return 0.999
    if form1 == 'trivial':
        return 0.001
    if form1 == 'singleton':
        return 0.999
    if form1 == 'absorbing':
        return 0.999

    # Direct substitution check
    s = {}
    if match_trees(eq1[0], eq2[0], s) and match_trees(eq1[1], eq2[1], s):
        return 0.999
    s = {}
    if match_trees(eq1[1], eq2[0], s) and match_trees(eq1[0], eq2[1], s):
        return 0.999

    # General form NEVER implies lhs_var/absorbing/singleton
    if form1 == 'general' and form2 in ('lhs_var', 'absorbing', 'singleton'):
        return 0.001

    # Signature direction: lhs_ops > 0 never implies lhs_ops = 0 (except trivial)
    if sig1[0] > 0 and sig2[0] == 0 and sig2[1] > 0:
        return 0.001

    # sig(2,2) only implies sig(2,2) or trivial
    if sig1[0] == 2 and sig2[0] < 2 and form2 != 'trivial':
        return 0.001

    # lhs_ops(2) never implies lhs_ops(1)
    if sig1[0] == 2 and sig2[0] == 1:
        return 0.001

    # BFS rewriting to check implication
    rules = [(eq1[0], eq1[1]), (eq1[1], eq1[0])]
    try:
        reachable_lhs = bfs_rewrite(eq2[0], rules, limit=200)
        reachable_rhs = bfs_rewrite(eq2[1], rules, limit=200)
        if not reachable_lhs.isdisjoint(reachable_rhs):
            return 0.99
    except:
        pass

    # Counterexample search
    try:
        if find_counterexample(eq1, eq2):
            return 0.001
    except:
        pass

    # Linear magma counterexample (polynomial method)
    # x*y = ax + by mod p
    for p in [2, 3, 5, 7]:
        for a in range(p):
            for b in range(p):
                table = [[(a*r + b*c) % p for c in range(p)] for r in range(p)]
                try:
                    if check_magma(eq1, table) and not check_magma(eq2, table):
                        return 0.001
                except:
                    pass

    # 1-var and 2-var lhs_var equations
    if form1 == 'lhs_var' and nvars1 == 1 and nvars2 >= 2:
        return 0.01
    if form1 == 'lhs_var' and nvars1 == 2:
        if nvars2 >= 3:
            return 0.01
        if nvars2 == 2:
            return 0.02

    # Variable count based probability
    nvd = nvars1 - nvars2

    # Calibrated probabilities based on analysis
    if form1 == 'lhs_var' and form2 == 'lhs_var':
        prob_map = {-4: 0.001, -3: 0.04, -2: 0.10, -1: 0.21, 0: 0.34, 1: 0.50, 2: 0.62, 3: 0.71, 4: 0.82}
        p = prob_map.get(nvd, 0.37 if nvd == 0 else (0.82 if nvd > 4 else 0.001))
        return p

    if form1 == 'lhs_var' and form2 == 'general':
        prob_map = {-4: 0.001, -3: 0.04, -2: 0.11, -1: 0.22, 0: 0.36, 1: 0.51, 2: 0.65, 3: 0.74}
        p = prob_map.get(nvd, 0.37 if nvd == 0 else (0.74 if nvd > 3 else 0.001))
        return p

    if form1 == 'general' and form2 == 'general':
        prob_map = {-4: 0.001, -3: 0.04, -2: 0.09, -1: 0.18, 0: 0.30, 1: 0.43, 2: 0.55, 3: 0.63, 4: 0.67}
        p = prob_map.get(nvd, 0.37 if nvd == 0 else (0.67 if nvd > 4 else 0.001))
        return p

    # Default calibrated by nvars_diff
    prob_map = {-4: 0.001, -3: 0.04, -2: 0.11, -1: 0.21, 0: 0.33, 1: 0.49, 2: 0.61, 3: 0.69, 4: 0.74}
    p = prob_map.get(nvd, 0.37 if nvd == 0 else (0.74 if nvd > 4 else 0.001))
    return p

# Evaluate on random sample
print("=== EVALUATING V2 PREDICTOR ===")
random.seed(42)
sample_size = 50000
indices = [(random.randint(0, len(equations)-1), random.randint(0, len(equations)-1))
           for _ in range(sample_size)]

correct = wrong = total = 0
ll_sum = 0.0
tp = fp = tn = fn = 0

for i, j in indices:
    if i == j: continue
    total += 1
    actual = M[i][j] > 0
    p = predict_implication_v2(equations[i], equations[j])
    pred = p > 0.5

    if pred == actual: correct += 1
    else: wrong += 1
    if pred and actual: tp += 1
    elif pred and not actual: fp += 1
    elif not pred and not actual: tn += 1
    else: fn += 1

    p_clamp = max(1e-9, min(1-1e-9, p))
    ll_sum += math.log(p_clamp) if actual else math.log(1 - p_clamp)

print(f"Total: {total}")
print(f"Accuracy: {correct/total:.4f}")
print(f"Avg log-likelihood: {ll_sum/total:.4f}")
print(f"TP={tp}, FP={fp}, TN={tn}, FN={fn}")

# Test on short_test
print("\n=== SHORT TEST ===")
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
ll_sum = 0.0
for law1, law2, actual in short_test:
    p = predict_implication_v2(law1, law2)
    pred = p > 0.5
    is_correct = pred == actual
    test_correct += is_correct

    p_clamp = max(1e-9, min(1-1e-9, p))
    ll = math.log(p_clamp) if actual else math.log(1-p_clamp)
    ll_sum += ll

    status = "✓" if is_correct else "✗"
    print(f"  {status} p={p:.3f}, pred={pred}, actual={actual}: {law1[:40]}...")

print(f"\nAccuracy: {test_correct}/20 = {test_correct/20:.2f}")
print(f"Avg LL: {ll_sum/20:.4f}")

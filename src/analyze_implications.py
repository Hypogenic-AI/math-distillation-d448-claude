"""Analyze the implication graph to extract patterns for cheatsheet design."""
import numpy as np
import json
import re
import sys
from collections import Counter, defaultdict

DATA_DIR = "/workspaces/math-distillation-d448-claude/code/equational_theories/data"
PRED_DIR = "/workspaces/math-distillation-d448-claude/code/equational_theories/scripts/predictor"

# Load equations
with open(f"{PRED_DIR}/equations.txt") as f:
    equations = [line.strip() for line in f if line.strip()]
print(f"Loaded {len(equations)} equations")

# Load implication matrix
import pandas as pd
df = pd.read_csv(f"{PRED_DIR}/raw_implications.csv", header=None)
matrix = df.values
print(f"Matrix shape: {matrix.shape}")

# Positive values = implication holds, negative = doesn't hold
# Count true/false
true_count = np.sum(matrix > 0)
false_count = np.sum(matrix < 0)
total = true_count + false_count
print(f"\nTrue implications: {true_count} ({100*true_count/total:.2f}%)")
print(f"False implications: {false_count} ({100*false_count/total:.2f}%)")

# Parse equation structure
def parse_eq(s):
    """Parse equation string into (lhs, rhs) where each is a tree."""
    sides = s.split('=')
    lhs = sides[0].strip()
    rhs = sides[1].strip()
    return lhs, rhs

def count_vars(s):
    """Count distinct variables in equation string."""
    return len(set(re.findall(r'[a-z]', s)))

def count_ops(s):
    """Count operation symbols in equation string."""
    return s.count('*') + s.count('◇')

def get_signature(s):
    """Get (lhs_ops, rhs_ops) signature."""
    lhs, rhs = s.split('=')
    lhs_ops = lhs.count('*') + lhs.count('◇')
    rhs_ops = rhs.count('*') + rhs.count('◇')
    return (lhs_ops, rhs_ops)

def get_var_counts_per_side(s):
    """Get variable counts on each side."""
    lhs, rhs = s.split('=')
    lhs_vars = set(re.findall(r'[a-z]', lhs))
    rhs_vars = set(re.findall(r'[a-z]', rhs))
    return lhs_vars, rhs_vars

# Analyze equation features
features = []
for i, eq in enumerate(equations):
    nvars = count_vars(eq)
    nops = count_ops(eq)
    sig = get_signature(eq)
    lv, rv = get_var_counts_per_side(eq)
    features.append({
        'idx': i,
        'eq': eq,
        'nvars': nvars,
        'nops': nops,
        'sig': sig,
        'lhs_vars': lv,
        'rhs_vars': rv,
        'lhs_only_vars': lv - rv,
        'rhs_only_vars': rv - lv,
    })

# Find equivalence classes
print("\n=== EQUIVALENCE CLASSES ===")
equiv_classes = defaultdict(list)
for i in range(len(equations)):
    for j in range(i+1, len(equations)):
        if matrix[i][j] > 0 and matrix[j][i] > 0:
            # i and j are equivalent - use union-find later
            pass

# Simpler: find which equations imply E2 (x=y, index 1)
e2_implies = []  # equations that E2 implies (everything)
implies_e2 = []  # equations implied by everything (equivalent to E2)
for i in range(len(equations)):
    if matrix[i][1] > 0:  # equation i implies E2
        implies_e2.append(i)

print(f"Equations that imply E2 (x=y): {len(implies_e2)}")

# E1 = x=x (index 0) - trivial, implied by everything
e1_implied_by = sum(1 for i in range(len(equations)) if matrix[i][0] > 0)
print(f"Equations implying E1 (x=x): {e1_implied_by}")

# Analyze patterns by variable count
print("\n=== IMPLICATION PATTERNS BY VARIABLE COUNT ===")
for nv1 in range(1, 6):
    for nv2 in range(1, 6):
        true_c = 0
        false_c = 0
        for i in range(len(equations)):
            if features[i]['nvars'] != nv1:
                continue
            for j in range(len(equations)):
                if features[j]['nvars'] != nv2:
                    continue
                if i == j:
                    continue
                if matrix[i][j] > 0:
                    true_c += 1
                elif matrix[i][j] < 0:
                    false_c += 1
        total_c = true_c + false_c
        if total_c > 0:
            print(f"  vars({nv1}) -> vars({nv2}): {true_c}/{total_c} = {100*true_c/total_c:.1f}% true")

# Analyze patterns by signature
print("\n=== IMPLICATION PATTERNS BY SIGNATURE ===")
sig_stats = defaultdict(lambda: [0, 0])
for i in range(len(equations)):
    for j in range(len(equations)):
        if i == j:
            continue
        sig_i = features[i]['sig']
        sig_j = features[j]['sig']
        key = (sig_i, sig_j)
        if matrix[i][j] > 0:
            sig_stats[key][0] += 1
        elif matrix[i][j] < 0:
            sig_stats[key][1] += 1

# Print top signature pairs by count
sorted_sigs = sorted(sig_stats.items(), key=lambda x: sum(x[1]), reverse=True)[:30]
for (s1, s2), (t, f) in sorted_sigs:
    total_s = t + f
    print(f"  sig{s1} -> sig{s2}: {t}/{total_s} = {100*t/total_s:.1f}% true")

# Analyze: does operation count difference predict implication?
print("\n=== OPS DIFFERENCE ANALYSIS ===")
ops_diff_stats = defaultdict(lambda: [0, 0])
for i in range(len(equations)):
    for j in range(len(equations)):
        if i == j:
            continue
        diff = features[i]['nops'] - features[j]['nops']
        if matrix[i][j] > 0:
            ops_diff_stats[diff][0] += 1
        elif matrix[i][j] < 0:
            ops_diff_stats[diff][1] += 1

for diff in sorted(ops_diff_stats.keys()):
    t, f = ops_diff_stats[diff]
    total_d = t + f
    print(f"  ops_diff={diff:+d}: {t}/{total_d} = {100*t/total_d:.1f}% true")

# Key insight: what fraction of equations with x on LHS and expression on RHS imply E2?
print("\n=== SIMPLE FORM ANALYSIS ===")
simple_form = []  # equations of form x = f(...)
for i, f in enumerate(features):
    lhs, rhs = equations[i].split('=')
    lhs = lhs.strip()
    rhs = rhs.strip()
    if re.match(r'^[a-z]$', lhs):  # LHS is a single variable
        simple_form.append(i)

print(f"Equations of form 'x = ...' : {len(simple_form)} out of {len(equations)}")

# Check: for form "x = f(y, z, ...)" where x doesn't appear in RHS
# These should imply E2 (x=y) because we can substitute any value for x
absorbing = []
for i in simple_form:
    lhs, rhs = equations[i].split('=')
    lhs_var = lhs.strip()
    rhs = rhs.strip()
    rhs_vars = set(re.findall(r'[a-z]', rhs))
    if lhs_var not in rhs_vars and len(rhs_vars) > 0:
        absorbing.append(i)
        # Verify against matrix
        implies_e2_check = matrix[i][1] > 0
        if not implies_e2_check:
            print(f"  UNEXPECTED: E{i+1} ({equations[i]}) does NOT imply E2!")

print(f"Equations 'x = f(other vars only)': {len(absorbing)} - all should imply E2")

# Analyze variable overlap between LHS and RHS
print("\n=== VARIABLE OVERLAP ANALYSIS ===")
lhs_only_stats = defaultdict(lambda: [0, 0])
for i in range(len(equations)):
    has_lhs_only = len(features[i]['lhs_only_vars']) > 0
    has_rhs_only = len(features[i]['rhs_only_vars']) > 0
    for j in range(len(equations)):
        if i == j:
            continue
        if matrix[i][j] > 0:
            lhs_only_stats[(has_lhs_only, has_rhs_only)][0] += 1
        elif matrix[i][j] < 0:
            lhs_only_stats[(has_lhs_only, has_rhs_only)][1] += 1

for (lo, ro), (t, f) in sorted(lhs_only_stats.items()):
    total_l = t + f
    print(f"  premise has lhs_only={lo}, rhs_only={ro}: {t}/{total_l} = {100*t/total_l:.1f}% true")

print("\nDone with analysis!")

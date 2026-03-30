"""Deeper analysis of implication patterns for cheatsheet design."""
import numpy as np
import re
import json
from collections import defaultdict

DATA_DIR = "/workspaces/math-distillation-d448-claude/code/equational_theories/data"
PRED_DIR = "/workspaces/math-distillation-d448-claude/code/equational_theories/scripts/predictor"

with open(f"{PRED_DIR}/equations.txt") as f:
    equations = [line.strip() for line in f if line.strip()]

import pandas as pd
df = pd.read_csv(f"{PRED_DIR}/raw_implications.csv", header=None)
matrix = df.values

# Load duals
with open(f"{DATA_DIR}/duals.json") as f:
    duals_data = json.load(f)
dual_map = {}
for pair in duals_data:
    dual_map[pair[0]] = pair[1]
    dual_map[pair[1]] = pair[0]
print(f"Dual pairs: {len(duals_data)}")

def get_signature(s):
    lhs, rhs = s.split('=')
    lhs_ops = lhs.count('*') + lhs.count('◇')
    rhs_ops = rhs.count('*') + rhs.count('◇')
    return (lhs_ops, rhs_ops)

def count_vars(s):
    return len(set(re.findall(r'[a-z]', s)))

def get_var_multiset(s):
    """Get sorted tuple of per-variable occurrence counts."""
    side_parts = s.split('=')
    lhs, rhs = side_parts[0], side_parts[1]
    all_vars = set(re.findall(r'[a-z]', s))
    lhs_counts = {}
    rhs_counts = {}
    for v in re.findall(r'[a-z]', lhs):
        lhs_counts[v] = lhs_counts.get(v, 0) + 1
    for v in re.findall(r'[a-z]', rhs):
        rhs_counts[v] = rhs_counts.get(v, 0) + 1
    return lhs_counts, rhs_counts

# KEY FINDING: signature(1,x) or (2,x) NEVER implies signature(0,y)
# This is a huge rule! Let's verify and quantify.
print("=== SIGNATURE DIRECTION RULES ===")
print("Testing: does sig with LHS ops > 0 ever imply sig with LHS ops = 0?")
for lhs_ops_1 in [1, 2]:
    for lhs_ops_2 in [0]:
        count_true = 0
        count_false = 0
        for i in range(len(equations)):
            sig_i = get_signature(equations[i])
            if sig_i[0] != lhs_ops_1:
                continue
            for j in range(len(equations)):
                sig_j = get_signature(equations[j])
                if sig_j[0] != lhs_ops_2:
                    continue
                if matrix[i][j] > 0:
                    count_true += 1
                elif matrix[i][j] < 0:
                    count_false += 1
        print(f"  lhs_ops={lhs_ops_1} -> lhs_ops={lhs_ops_2}: true={count_true}, false={count_false}")

# Analyze: "x = f(vars)" form where LHS is single variable
print("\n=== FORM-BASED RULES ===")
def classify_form(eq):
    """Classify equation into structural forms."""
    lhs, rhs = eq.split('=')
    lhs = lhs.strip()
    rhs = rhs.strip()

    lhs_is_var = bool(re.match(r'^[a-z]$', lhs))
    rhs_is_var = bool(re.match(r'^[a-z]$', rhs))

    if lhs_is_var and rhs_is_var:
        if lhs == rhs:
            return 'trivial'  # x = x
        return 'singleton'  # x = y

    lhs_vars = set(re.findall(r'[a-z]', lhs))
    rhs_vars = set(re.findall(r'[a-z]', rhs))

    if lhs_is_var:
        lhs_var = lhs
        if lhs_var not in rhs_vars:
            return 'absorbing'  # x = f(y,z,...) where x not in RHS
        return 'lhs_var'  # x = f(x, y, ...)

    if rhs_is_var:
        rhs_var = rhs
        if rhs_var not in lhs_vars:
            return 'absorbing_r'  # f(y,z,...) = x where x not in LHS
        return 'rhs_var'  # f(x, y, ...) = x

    return 'general'  # f(...) = g(...)

form_counts = defaultdict(int)
form_indices = defaultdict(list)
for i, eq in enumerate(equations):
    form = classify_form(eq)
    form_counts[form] += 1
    form_indices[form].append(i)

print("Form distribution:")
for form, count in sorted(form_counts.items(), key=lambda x: -x[1]):
    print(f"  {form}: {count}")

# Key rule: absorbing equations all imply E2
print(f"\nAbsorbing equations: {form_counts['absorbing']} + {form_counts.get('absorbing_r', 0)}")

# Analyze implication rates between forms
print("\n=== CROSS-FORM IMPLICATION RATES ===")
forms = ['trivial', 'singleton', 'absorbing', 'lhs_var', 'rhs_var', 'general']
for f1 in forms:
    for f2 in forms:
        if not form_indices[f1] or not form_indices[f2]:
            continue
        true_c = 0
        false_c = 0
        # Sample if too many
        idx1 = form_indices[f1]
        idx2 = form_indices[f2]
        for i in idx1:
            for j in idx2:
                if i == j:
                    continue
                if matrix[i][j] > 0:
                    true_c += 1
                elif matrix[i][j] < 0:
                    false_c += 1
        total_c = true_c + false_c
        if total_c > 0:
            print(f"  {f1:12s} -> {f2:12s}: {true_c:8d}/{total_c:8d} = {100*true_c/total_c:.1f}%")

# Analyze: variable multiplicity patterns
print("\n=== VARIABLE MULTIPLICITY ANALYSIS ===")
def get_var_profile(eq):
    """Get a canonical profile of variable occurrences per side."""
    lhs, rhs = eq.split('=')
    lhs_vars = re.findall(r'[a-z]', lhs)
    rhs_vars = re.findall(r'[a-z]', rhs)
    all_vars = sorted(set(lhs_vars + rhs_vars))
    profile = []
    for v in all_vars:
        lc = lhs_vars.count(v)
        rc = rhs_vars.count(v)
        profile.append((lc, rc))
    return tuple(sorted(profile))

# Check: if multiplicity profiles don't match in certain ways, implication fails
# Specifically: in a magma satisfying E1, if we look at the "total variable count" patterns

# Let's look at a more specific question:
# For equations of form "x = ..." (LHS is single var):
# How does the number of distinct vars in RHS affect implication?
print("\n=== RHS VARIABLE COUNT FOR 'x = ...' FORM ===")
for nv1 in range(1, 6):
    for nv2 in range(1, 6):
        true_c = 0
        false_c = 0
        for i in form_indices['lhs_var']:
            lhs1, rhs1 = equations[i].split('=')
            rhs1_nvars = len(set(re.findall(r'[a-z]', rhs1)))
            if rhs1_nvars != nv1:
                continue
            for j in form_indices['lhs_var']:
                if i == j:
                    continue
                lhs2, rhs2 = equations[j].split('=')
                rhs2_nvars = len(set(re.findall(r'[a-z]', rhs2)))
                if rhs2_nvars != nv2:
                    continue
                if matrix[i][j] > 0:
                    true_c += 1
                elif matrix[i][j] < 0:
                    false_c += 1
        total_c = true_c + false_c
        if total_c > 0:
            pct = 100*true_c/total_c
            if pct > 60 or pct < 5:
                marker = " <---"
            else:
                marker = ""
            print(f"  rhs_vars({nv1}) -> rhs_vars({nv2}): {true_c}/{total_c} = {pct:.1f}%{marker}")

# Check self-dual equations and their special properties
print("\n=== SELF-DUAL EQUATIONS ===")
self_dual = []
for i in range(len(equations)):
    if i+1 in dual_map and dual_map[i+1] == i+1:
        self_dual.append(i)
# Also check equations not in dual_map (they might be self-dual)
print(f"Self-dual equations (in dual_map): {len(self_dual)}")

# Analyze: total operation count as a predictor
print("\n=== TOTAL OPERATION COUNT ANALYSIS ===")
for ops1 in range(0, 9):
    for ops2 in range(0, 9):
        true_c = 0
        false_c = 0
        for i in range(len(equations)):
            nops_i = equations[i].count('*') + equations[i].count('◇')
            if nops_i != ops1:
                continue
            for j in range(len(equations)):
                if i == j:
                    continue
                nops_j = equations[j].count('*') + equations[j].count('◇')
                if nops_j != ops2:
                    continue
                if matrix[i][j] > 0:
                    true_c += 1
                elif matrix[i][j] < 0:
                    false_c += 1
        total_c = true_c + false_c
        if total_c > 1000:
            pct = 100*true_c/total_c
            print(f"  ops({ops1}) -> ops({ops2}): {true_c:8d}/{total_c:8d} = {pct:.1f}%")

print("\nDone!")

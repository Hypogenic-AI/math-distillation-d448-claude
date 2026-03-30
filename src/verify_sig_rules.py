"""Verify specific signature-based rules and find more 100% rules."""
import numpy as np
import re
import json
from collections import defaultdict

PRED_DIR = "/workspaces/math-distillation-d448-claude/code/equational_theories/scripts/predictor"

with open(f"{PRED_DIR}/equations.txt") as f:
    equations = [line.strip() for line in f if line.strip()]

import pandas as pd
df = pd.read_csv(f"{PRED_DIR}/raw_implications.csv", header=None)
M = df.values

def get_sig(eq):
    lhs, rhs = eq.split('=')
    lhs_ops = lhs.count('*') + lhs.count('◇')
    rhs_ops = rhs.count('*') + rhs.count('◇')
    return (lhs_ops, rhs_ops)

# Check ALL signature pairs for 0% true rate (= can be safely predicted as False)
print("=== SIGNATURE PAIRS WITH 0% TRUE RATE ===")
sig_stats = defaultdict(lambda: [0, 0])
for i in range(len(equations)):
    si = get_sig(equations[i])
    for j in range(len(equations)):
        if i == j: continue
        sj = get_sig(equations[j])
        if M[i][j] > 0: sig_stats[(si, sj)][0] += 1
        else: sig_stats[(si, sj)][1] += 1

for (s1, s2) in sorted(sig_stats.keys()):
    t, f = sig_stats[(s1, s2)]
    total = t + f
    if total > 100:
        pct = 100*t/total
        if pct == 0 or pct > 99:
            print(f"  sig{s1}->sig{s2}: {t}/{total} = {pct:.1f}%")

# Key question: what's the relationship between LHS ops in premise and conclusion?
print("\n=== LHS OPS RELATIONSHIP ===")
for lo1 in range(4):
    for lo2 in range(4):
        t_count = 0
        f_count = 0
        for i in range(len(equations)):
            si = get_sig(equations[i])
            if si[0] != lo1: continue
            for j in range(len(equations)):
                if i == j: continue
                sj = get_sig(equations[j])
                if sj[0] != lo2: continue
                if M[i][j] > 0: t_count += 1
                else: f_count += 1
        total = t_count + f_count
        if total > 0:
            print(f"  lhs_ops({lo1})->lhs_ops({lo2}): {t_count}/{total} = {100*t_count/total:.1f}%")

# Verify: does sig(2,2) ever imply sig with lhs_ops < 2?
print("\n=== SIG(2,2) IMPLICATIONS ===")
for s2 in sorted(set(get_sig(eq) for eq in equations)):
    t_count = 0
    f_count = 0
    for i in range(len(equations)):
        if get_sig(equations[i]) != (2,2): continue
        for j in range(len(equations)):
            if i == j: continue
            if get_sig(equations[j]) != s2: continue
            if M[i][j] > 0: t_count += 1
            else: f_count += 1
    total = t_count + f_count
    if total > 0:
        print(f"  (2,2)->sig{s2}: {t_count}/{total} = {100*t_count/total:.1f}%")

# Check: does sig(1,3) ever imply sig with lhs_ops != 1?
print("\n=== SIG(1,3) IMPLICATIONS ===")
for s2 in sorted(set(get_sig(eq) for eq in equations)):
    t_count = 0
    f_count = 0
    for i in range(len(equations)):
        if get_sig(equations[i]) != (1,3): continue
        for j in range(len(equations)):
            if i == j: continue
            if get_sig(equations[j]) != s2: continue
            if M[i][j] > 0: t_count += 1
            else: f_count += 1
    total = t_count + f_count
    if total > 0:
        print(f"  (1,3)->sig{s2}: {t_count}/{total} = {100*t_count/total:.1f}%")

# Key: among lhs_var equations with 2 vars, what's the implication rate?
print("\n=== 2-VAR LHS_VAR ANALYSIS ===")
def is_lhs_var_form(eq):
    lhs, rhs = eq.split('=')
    lhs = lhs.strip()
    rhs = rhs.strip()
    if not re.match(r'^[a-z]$', lhs): return False
    rhs_vars = set(re.findall(r'[a-z]', rhs))
    return lhs in rhs_vars

two_var_lhsvar = [i for i in range(len(equations))
                   if is_lhs_var_form(equations[i])
                   and len(set(re.findall(r'[a-z]', equations[i]))) == 2]
print(f"2-var lhs_var equations: {len(two_var_lhsvar)}")

# What do these rarely imply?
for nv2 in range(1, 6):
    t_c = 0
    f_c = 0
    for i in two_var_lhsvar:
        for j in range(len(equations)):
            if i == j: continue
            nvj = len(set(re.findall(r'[a-z]', equations[j])))
            if nvj != nv2: continue
            if M[i][j] > 0: t_c += 1
            else: f_c += 1
    total = t_c + f_c
    if total > 0:
        print(f"  2var_lhsvar -> {nv2}var: {t_c}/{total} = {100*t_c/total:.1f}%")

# Now let's check: is there a pattern with "idempotent" form x = x * x?
print("\n=== IDEMPOTENT LAW (x = x * x, or x * x = x) ===")
idemp_idx = None
for i, eq in enumerate(equations):
    eq_clean = eq.replace(' ', '').replace('◇', '*')
    if eq_clean in ['x=x*x', 'x*x=x']:
        print(f"  E{i+1}: {eq}")
        idemp_idx = i

# Check what E3 (x = x*x) implies
if idemp_idx is not None:
    implies = []
    for j in range(len(equations)):
        if idemp_idx == j: continue
        if M[idemp_idx][j] > 0:
            implies.append(j)
    print(f"  E{idemp_idx+1} implies {len(implies)} equations")
    implied_by = sum(1 for i in range(len(equations)) if i != idemp_idx and M[i][idemp_idx] > 0)
    print(f"  E{idemp_idx+1} is implied by {implied_by} equations")

print("\nDone!")

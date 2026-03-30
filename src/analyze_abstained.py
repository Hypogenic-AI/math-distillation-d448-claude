"""Analyze the abstained cases to find additional predictive features."""
import numpy as np
import re
import json
from collections import defaultdict

PRED_DIR = "/workspaces/math-distillation-d448-claude/code/equational_theories/scripts/predictor"
DATA_DIR = "/workspaces/math-distillation-d448-claude/code/equational_theories/data"

with open(f"{PRED_DIR}/equations.txt") as f:
    equations = [line.strip() for line in f if line.strip()]

import pandas as pd
df = pd.read_csv(f"{PRED_DIR}/raw_implications.csv", header=None)
M = df.values

def parse_eq(s):
    sides = s.split('=')
    return sides[0].strip(), sides[1].strip()

def is_single_var(s):
    return bool(re.match(r'^[a-z]$', s.strip()))

def get_vars(s):
    return set(re.findall(r'[a-z]', s))

def count_ops(s):
    return s.count('*') + s.count('◇')

def get_sig(eq):
    lhs, rhs = parse_eq(eq)
    return (count_ops(lhs), count_ops(rhs))

def get_form(eq):
    lhs, rhs = parse_eq(eq)
    lhs_var = is_single_var(lhs)
    rhs_var = is_single_var(rhs)
    if lhs_var and rhs_var:
        if lhs.strip() == rhs.strip():
            return 'trivial'
        return 'singleton'
    lhs_vars = get_vars(lhs)
    rhs_vars = get_vars(rhs)
    if lhs_var:
        if lhs.strip() not in rhs_vars:
            return 'absorbing'
        return 'lhs_var'
    if rhs_var:
        if rhs.strip() not in lhs_vars:
            return 'absorbing_r'
        return 'rhs_var'
    return 'general'

# Build features
feats = []
for i, eq in enumerate(equations):
    lhs, rhs = parse_eq(eq)
    feats.append({
        'form': get_form(eq),
        'sig': get_sig(eq),
        'nvars': len(get_vars(eq)),
        'lhs_vars': get_vars(lhs),
        'rhs_vars': get_vars(rhs),
    })

def combined_rule(i, j):
    if feats[j]['form'] == 'trivial': return True
    if feats[i]['form'] == 'trivial': return False
    if feats[i]['form'] == 'singleton': return True
    if feats[i]['form'] == 'absorbing': return True
    if feats[i]['form'] == 'general':
        if feats[j]['form'] in ('lhs_var', 'absorbing', 'singleton'):
            return False
    sig_i = feats[i]['sig']
    sig_j = feats[j]['sig']
    if sig_i[0] > 0 and sig_j[0] == 0:
        return False
    if feats[i]['form'] == 'lhs_var' and feats[j]['form'] == 'lhs_var':
        if feats[i]['nvars'] == 1 and feats[j]['nvars'] >= 2:
            return False
    return None

# For abstained cases, analyze MORE features
# Focus: among same-variable-count pairs, what predicts implication?

# Feature: variable occurrence pattern per side
def get_var_occ_profile(eq):
    """For each variable, count occurrences on LHS and RHS."""
    lhs, rhs = parse_eq(eq)
    all_vars = sorted(get_vars(eq))
    profile = []
    for v in all_vars:
        lc = lhs.count(v)  # approximate - counts in substrings too
        rc = rhs.count(v)
        profile.append((lc, rc))
    return tuple(sorted(profile))

# Feature: total variable occurrences on each side
def get_total_var_occ(eq):
    lhs, rhs = parse_eq(eq)
    lhs_total = len(re.findall(r'[a-z]', lhs))
    rhs_total = len(re.findall(r'[a-z]', rhs))
    return lhs_total, rhs_total

# Feature: depth of operation nesting
def get_depth(s):
    """Get max nesting depth."""
    depth = 0
    max_depth = 0
    for c in s:
        if c == '(':
            depth += 1
            max_depth = max(max_depth, depth)
        elif c == ')':
            depth -= 1
    return max_depth

# Analyze abstained cases by signature pair
print("=== ABSTAINED: SIGNATURE PAIR ANALYSIS ===")
sig_stats = defaultdict(lambda: [0, 0])
for i in range(len(equations)):
    for j in range(len(equations)):
        if i == j: continue
        if combined_rule(i, j) is not None: continue
        key = (feats[i]['sig'], feats[j]['sig'])
        if M[i][j] > 0:
            sig_stats[key][0] += 1
        else:
            sig_stats[key][1] += 1

sorted_sigs = sorted(sig_stats.items(), key=lambda x: sum(x[1]), reverse=True)[:20]
for (s1, s2), (t, f) in sorted_sigs:
    total = t + f
    print(f"  sig{s1}->sig{s2}: {t}/{total} = {100*t/total:.1f}%")

# Analyze: does (total_ops_diff, nvars_diff) predict well?
print("\n=== ABSTAINED: (nvars_diff, lhs_sig_match) ===")
for nvd in range(-2, 4):
    for sig_match in [True, False]:
        t_count = 0
        f_count = 0
        for i in range(len(equations)):
            for j in range(len(equations)):
                if i == j: continue
                if combined_rule(i, j) is not None: continue
                ni = feats[i]['nvars']
                nj = feats[j]['nvars']
                if ni - nj != nvd: continue
                sm = (feats[i]['sig'][0] == feats[j]['sig'][0])
                if sm != sig_match: continue
                if M[i][j] > 0: t_count += 1
                else: f_count += 1
        total = t_count + f_count
        if total > 5000:
            print(f"  nvars_diff={nvd:+d}, same_lhs_sig={sig_match}: {t_count}/{total} = {100*t_count/total:.1f}%")

# Check: among abstained, does the "conclusion has fewer vars than premise" pattern hold?
print("\n=== ABSTAINED: DETAILED VAR OCC ANALYSIS ===")
# Total var occurrences (counting repetitions)
occ_diff_stats = defaultdict(lambda: [0, 0])
for i in range(len(equations)):
    tvo_i = get_total_var_occ(equations[i])
    for j in range(len(equations)):
        if i == j: continue
        if combined_rule(i, j) is not None: continue
        tvo_j = get_total_var_occ(equations[j])
        # Total occurrences in eq i vs eq j
        total_i = sum(tvo_i)
        total_j = sum(tvo_j)
        diff = total_i - total_j
        if M[i][j] > 0: occ_diff_stats[diff][0] += 1
        else: occ_diff_stats[diff][1] += 1

print("Total var occurrences diff (among abstained):")
for diff in sorted(occ_diff_stats.keys()):
    t, f = occ_diff_stats[diff]
    total = t + f
    if total > 5000:
        print(f"  total_occ_diff={diff:+d}: {t}/{total} = {100*t/total:.1f}%")

# Check depth difference
print("\n=== ABSTAINED: DEPTH ANALYSIS ===")
depth_stats = defaultdict(lambda: [0, 0])
for i in range(len(equations)):
    di = get_depth(equations[i])
    for j in range(len(equations)):
        if i == j: continue
        if combined_rule(i, j) is not None: continue
        dj = get_depth(equations[j])
        diff = di - dj
        if M[i][j] > 0: depth_stats[diff][0] += 1
        else: depth_stats[diff][1] += 1

for diff in sorted(depth_stats.keys()):
    t, f = depth_stats[diff]
    total = t + f
    if total > 1000:
        print(f"  depth_diff={diff:+d}: {t}/{total} = {100*t/total:.1f}%")

# Among general -> general (abstained), analyze
print("\n=== GENERAL->GENERAL ABSTAINED ===")
gg_var_stats = defaultdict(lambda: [0, 0])
for i in range(len(equations)):
    if feats[i]['form'] != 'general': continue
    for j in range(len(equations)):
        if i == j: continue
        if feats[j]['form'] != 'general': continue
        if combined_rule(i, j) is not None: continue
        nvd = feats[i]['nvars'] - feats[j]['nvars']
        if M[i][j] > 0: gg_var_stats[nvd][0] += 1
        else: gg_var_stats[nvd][1] += 1

for diff in sorted(gg_var_stats.keys()):
    t, f = gg_var_stats[diff]
    total = t + f
    if total > 1000:
        print(f"  general->general nvars_diff={diff:+d}: {t}/{total} = {100*t/total:.1f}%")

# Among lhs_var -> general (abstained), analyze
print("\n=== LHS_VAR->GENERAL ABSTAINED ===")
lg_stats = defaultdict(lambda: [0, 0])
for i in range(len(equations)):
    if feats[i]['form'] != 'lhs_var': continue
    for j in range(len(equations)):
        if i == j: continue
        if feats[j]['form'] != 'general': continue
        if combined_rule(i, j) is not None: continue
        nvd = feats[i]['nvars'] - feats[j]['nvars']
        if M[i][j] > 0: lg_stats[nvd][0] += 1
        else: lg_stats[nvd][1] += 1

for diff in sorted(lg_stats.keys()):
    t, f = lg_stats[diff]
    total = t + f
    if total > 1000:
        print(f"  lhs_var->general nvars_diff={diff:+d}: {t}/{total} = {100*t/total:.1f}%")

# Among lhs_var -> lhs_var (abstained), analyze by nvars of each
print("\n=== LHS_VAR->LHS_VAR ABSTAINED (by nvars pair) ===")
ll_stats = defaultdict(lambda: [0, 0])
for i in range(len(equations)):
    if feats[i]['form'] != 'lhs_var': continue
    for j in range(len(equations)):
        if i == j: continue
        if feats[j]['form'] != 'lhs_var': continue
        if combined_rule(i, j) is not None: continue
        key = (feats[i]['nvars'], feats[j]['nvars'])
        if M[i][j] > 0: ll_stats[key][0] += 1
        else: ll_stats[key][1] += 1

for key in sorted(ll_stats.keys()):
    t, f = ll_stats[key]
    total = t + f
    if total > 1000:
        print(f"  lhs_var(nvars={key[0]})->lhs_var(nvars={key[1]}): {t}/{total} = {100*t/total:.1f}%")

print("\nDone!")

"""Extract precise rules for the cheatsheet by analyzing the implication matrix."""
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

with open(f"{DATA_DIR}/duals.json") as f:
    duals_data = json.load(f)
dual_map = {}
for pair in duals_data:
    dual_map[pair[0]-1] = pair[1]-1  # Convert to 0-indexed
    dual_map[pair[1]-1] = pair[0]-1

def parse_eq(s):
    """Parse equation into components."""
    sides = s.split('=')
    lhs = sides[0].strip()
    rhs = sides[1].strip()
    return lhs, rhs

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

# Build features for each equation
feats = []
for i, eq in enumerate(equations):
    lhs, rhs = parse_eq(eq)
    lhs_vars = get_vars(lhs)
    rhs_vars = get_vars(rhs)
    all_vars = lhs_vars | rhs_vars
    sig = get_sig(eq)
    form = get_form(eq)

    # Var occurrence counts per side
    lhs_var_counts = {}
    for v in re.findall(r'[a-z]', lhs):
        lhs_var_counts[v] = lhs_var_counts.get(v, 0) + 1
    rhs_var_counts = {}
    for v in re.findall(r'[a-z]', rhs):
        rhs_var_counts[v] = rhs_var_counts.get(v, 0) + 1

    # Multiset of occurrences
    lhs_occ = sorted(lhs_var_counts.values())
    rhs_occ = sorted(rhs_var_counts.values())

    feats.append({
        'eq': eq,
        'form': form,
        'sig': sig,
        'nvars': len(all_vars),
        'total_ops': count_ops(eq),
        'lhs_vars': lhs_vars,
        'rhs_vars': rhs_vars,
        'all_vars': all_vars,
        'lhs_only': lhs_vars - rhs_vars,
        'rhs_only': rhs_vars - lhs_vars,
        'lhs_occ': tuple(lhs_occ),
        'rhs_occ': tuple(rhs_occ),
    })

# ============================================================
# RULE TESTING FRAMEWORK
# ============================================================
def test_rule(name, predict_fn):
    """Test a rule: predict_fn(i, j) returns True/False/None.
    True = predict implication, False = predict non-implication, None = abstain."""
    tp = fp = tn = fn = abstain = 0
    for i in range(len(equations)):
        for j in range(len(equations)):
            if i == j:
                continue
            pred = predict_fn(i, j)
            actual = M[i][j] > 0
            if pred is None:
                abstain += 1
            elif pred == True and actual == True:
                tp += 1
            elif pred == True and actual == False:
                fp += 1
            elif pred == False and actual == False:
                tn += 1
            elif pred == False and actual == True:
                fn += 1
    total = tp + fp + tn + fn
    coverage = total / (total + abstain) if total + abstain > 0 else 0
    accuracy = (tp + tn) / total if total > 0 else 0
    precision_t = tp / (tp + fp) if (tp + fp) > 0 else 0
    precision_f = tn / (tn + fn) if (tn + fn) > 0 else 0
    print(f"Rule: {name}")
    print(f"  Coverage: {coverage:.4f} ({total}/{total+abstain})")
    print(f"  Accuracy: {accuracy:.4f}")
    print(f"  True precision: {precision_t:.4f} (TP={tp}, FP={fp})")
    print(f"  False precision: {precision_f:.4f} (TN={tn}, FN={fn})")
    print(f"  Abstain: {abstain}")
    return {'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn, 'abstain': abstain}

# Rule 1: Trivial/singleton rules
def rule_trivial(i, j):
    if feats[i]['form'] == 'trivial':
        return False if i != j else None  # x=x implies nothing interesting
    if feats[j]['form'] == 'trivial':
        return True  # everything implies x=x
    if feats[i]['form'] == 'singleton':
        return True  # x=y implies everything
    if feats[j]['form'] == 'singleton':
        # Only absorbing and singleton imply x=y
        if feats[i]['form'] == 'absorbing':
            return True
        return None  # complex
    return None

print("=== RULE 1: Trivial/Singleton ===")
test_rule("trivial_singleton", rule_trivial)

# Rule 2: Absorbing equations imply everything
def rule_absorbing(i, j):
    if feats[i]['form'] == 'absorbing':
        return True
    return None

print("\n=== RULE 2: Absorbing ===")
test_rule("absorbing", rule_absorbing)

# Rule 3: General form never implies lhs_var/absorbing/singleton
def rule_general_never(i, j):
    if feats[i]['form'] == 'general':
        if feats[j]['form'] in ('lhs_var', 'absorbing', 'singleton'):
            return False
    return None

print("\n=== RULE 3: General never implies lhs_var/absorbing/singleton ===")
test_rule("general_never", rule_general_never)

# Rule 4: Signature LHS ops direction
# sig(a,b) where a>0 almost never implies sig(0,c)
def rule_sig_lhs(i, j):
    sig_i = feats[i]['sig']
    sig_j = feats[j]['sig']
    if sig_i[0] > 0 and sig_j[0] == 0:
        # Almost never true (1555 true out of ~5M false)
        return False
    return None

print("\n=== RULE 4: Signature LHS direction ===")
test_rule("sig_lhs_direction", rule_sig_lhs)

# Rule 5: Variable count direction (in lhs_var form)
# 1-var or 2-var RHS rarely implies 3+ var RHS
def rule_var_direction(i, j):
    if feats[i]['form'] == 'lhs_var' and feats[j]['form'] == 'lhs_var':
        ni = feats[i]['nvars']
        nj = feats[j]['nvars']
        if ni == 1 and nj >= 2:
            return False
        if ni == 2 and nj >= 3:
            return False
    return None

print("\n=== RULE 5: Variable count direction (lhs_var) ===")
test_rule("var_direction", rule_var_direction)

# Rule 6: Combined - more variables in premise means more likely to imply
def rule_var_count_heuristic(i, j):
    ni = feats[i]['nvars']
    nj = feats[j]['nvars']
    if ni >= 4 and nj <= 2:
        return True
    if ni <= 1 and nj >= 3:
        return False
    return None

print("\n=== RULE 6: Variable count heuristic ===")
test_rule("var_count_heuristic", rule_var_count_heuristic)

# Combined rule chain
def combined_rule(i, j):
    # R1: identity/singleton
    if feats[j]['form'] == 'trivial':
        return True
    if feats[i]['form'] == 'trivial':
        return False
    if feats[i]['form'] == 'singleton':
        return True
    if feats[i]['form'] == 'absorbing':
        return True

    # R2: general never implies non-general (except general and trivial)
    if feats[i]['form'] == 'general':
        if feats[j]['form'] in ('lhs_var', 'absorbing', 'singleton'):
            return False

    # R3: signature direction
    sig_i = feats[i]['sig']
    sig_j = feats[j]['sig']
    if sig_i[0] > 0 and sig_j[0] == 0:
        return False

    # R4: Variable count extremes
    ni = feats[i]['nvars']
    nj = feats[j]['nvars']
    if feats[i]['form'] == 'lhs_var' and feats[j]['form'] == 'lhs_var':
        if ni == 1 and nj >= 2:
            return False

    return None

print("\n=== COMBINED RULES ===")
r = test_rule("combined", combined_rule)
total_decided = r['tp'] + r['fp'] + r['tn'] + r['fn']
total_all = total_decided + r['abstain']
print(f"  Decided: {total_decided} / {total_all} = {total_decided/total_all:.4f}")

# For the abstained cases, what's the base rate?
abstain_true = 0
abstain_false = 0
for i in range(len(equations)):
    for j in range(len(equations)):
        if i == j:
            continue
        if combined_rule(i, j) is None:
            if M[i][j] > 0:
                abstain_true += 1
            else:
                abstain_false += 1
abstain_total = abstain_true + abstain_false
print(f"\n  Abstained base rate: {abstain_true}/{abstain_total} = {100*abstain_true/abstain_total:.1f}% true")

# For abstained: analyze what additional features help
print("\n=== ANALYSIS OF ABSTAINED CASES ===")
# Among abstained, check variable count pattern
var_stats = defaultdict(lambda: [0, 0])
for i in range(len(equations)):
    for j in range(len(equations)):
        if i == j:
            continue
        if combined_rule(i, j) is not None:
            continue
        ni = feats[i]['nvars']
        nj = feats[j]['nvars']
        diff = ni - nj
        if M[i][j] > 0:
            var_stats[diff][0] += 1
        else:
            var_stats[diff][1] += 1

print("Variable count difference (among abstained):")
for diff in sorted(var_stats.keys()):
    t, f = var_stats[diff]
    total_v = t + f
    if total_v > 1000:
        print(f"  nvars_diff={diff:+d}: {t}/{total_v} = {100*t/total_v:.1f}%")

print("\nDone!")

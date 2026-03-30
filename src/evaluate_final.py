"""Final evaluation of the predictor on various test sets."""
import numpy as np
import re
import json
import random
import math
import itertools
from collections import defaultdict

PRED_DIR = "/workspaces/math-distillation-d448-claude/code/equational_theories/scripts/predictor"

with open(f"{PRED_DIR}/equations.txt") as f:
    equations = [line.strip() for line in f if line.strip()]

import pandas as pd
df = pd.read_csv(f"{PRED_DIR}/raw_implications.csv", header=None)
M = df.values

# Import predictor
import sys
sys.path.insert(0, '/workspaces/math-distillation-d448-claude/src')
from improve_predictor import predict_implication_v2

# Evaluate on multiple random samples
print("=== LARGE SCALE EVALUATION ===")
random.seed(123)
total = correct = 0
ll_sum = 0.0
tp = fp = tn = fn = 0

for _ in range(200000):
    i = random.randint(0, len(equations)-1)
    j = random.randint(0, len(equations)-1)
    if i == j: continue
    total += 1
    actual = M[i][j] > 0
    p = predict_implication_v2(equations[i], equations[j])
    pred = p > 0.5

    if pred == actual: correct += 1
    if pred and actual: tp += 1
    elif pred and not actual: fp += 1
    elif not pred and not actual: tn += 1
    else: fn += 1

    p_c = max(1e-9, min(1-1e-9, p))
    ll_sum += math.log(p_c) if actual else math.log(1-p_c)

print(f"Total: {total}")
print(f"Accuracy: {correct/total:.4f}")
print(f"Avg LL: {ll_sum/total:.4f}")
print(f"TP={tp}, FP={fp}, TN={tn}, FN={fn}")
print(f"Precision(True): {tp/(tp+fp) if tp+fp else 0:.4f}")
print(f"Recall(True): {tp/(tp+fn) if tp+fn else 0:.4f}")
print(f"Precision(False): {tn/(tn+fn) if tn+fn else 0:.4f}")
print(f"Recall(False): {tn/(tn+fp) if tn+fp else 0:.4f}")

# "Always false" baseline
print(f"\nBaseline 'always false': accuracy = {(tn+fn+fp)/(total):.4f} (NOT right)")
base_false = sum(1 for _ in range(total) if True)  # wrong calc, fix:
actual_true = tp + fn
actual_false = tn + fp
print(f"Actual true: {actual_true}/{total} = {actual_true/total:.4f}")
print(f"Actual false: {actual_false}/{total} = {actual_false/total:.4f}")
print(f"'Always false' accuracy: {actual_false/total:.4f}")
print(f"Our improvement over 'always false': {correct/total - actual_false/total:+.4f}")

# Evaluate on the hard_triples if available
print("\n=== HARD TRIPLES EVALUATION ===")
try:
    sys.path.insert(0, PRED_DIR)
    from hard_triples import generated_triples
    ht_correct = 0
    ht_ll_sum = 0.0
    for law1, law2, actual in generated_triples:
        p = predict_implication_v2(law1, law2)
        pred = p > 0.5
        if pred == actual: ht_correct += 1
        p_c = max(1e-9, min(1-1e-9, p))
        ht_ll_sum += math.log(p_c) if actual else math.log(1-p_c)
    n = len(generated_triples)
    print(f"Hard triples: {ht_correct}/{n} = {ht_correct/n:.4f}")
    print(f"Hard triples avg LL: {ht_ll_sum/n:.4f}")
except Exception as e:
    print(f"Could not load hard_triples: {e}")

# Also test the generated_triples from short_test
print("\n=== ANALYZING ERRORS ===")
random.seed(456)
errors = []
for _ in range(50000):
    i = random.randint(0, len(equations)-1)
    j = random.randint(0, len(equations)-1)
    if i == j: continue
    actual = M[i][j] > 0
    p = predict_implication_v2(equations[i], equations[j])
    pred = p > 0.5
    if pred != actual:
        errors.append((i, j, actual, p))
        if len(errors) >= 20:
            break

print(f"Sample errors (first 20):")
for i, j, actual, p in errors[:20]:
    eq1 = equations[i]
    eq2 = equations[j]
    print(f"  E{i+1} -> E{j+1}: pred={p:.3f}, actual={actual}")
    print(f"    E{i+1}: {eq1}")
    print(f"    E{j+1}: {eq2}")

# Analyze: what fraction of errors are false negatives vs false positives?
print(f"\nTotal errors sampled: {len(errors)}")
fn_errors = [e for e in errors if e[2] == True]  # actual=True, pred=False
fp_errors = [e for e in errors if e[2] == False]  # actual=False, pred=True
print(f"False negatives (missed True): {len(fn_errors)}")
print(f"False positives (missed False): {len(fp_errors)}")

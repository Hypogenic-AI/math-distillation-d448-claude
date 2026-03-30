"""Analyze errors on hard triples to find improvement opportunities."""
import sys
sys.path.insert(0, '/workspaces/math-distillation-d448-claude/code/equational_theories/scripts/predictor')
sys.path.insert(0, '/workspaces/math-distillation-d448-claude/src')
from hard_triples import generated_triples
from final_predictor import predict_implication_v3, parse_equation, classify_form, get_sig, tree_vars
import math

fn_errors = []  # false negatives: actual=True, pred=False
fp_errors = []  # false positives: actual=False, pred=True

for law1, law2, actual in generated_triples:
    p = predict_implication_v3(law1, law2)
    pred = p > 0.5
    if pred != actual:
        if actual:
            fn_errors.append((law1, law2, p))
        else:
            fp_errors.append((law1, law2, p))

print(f"Total hard triples: {len(generated_triples)}")
print(f"False negatives (missed TRUE): {len(fn_errors)}")
print(f"False positives (missed FALSE): {len(fp_errors)}")

print("\n=== FALSE NEGATIVES (should be TRUE, predicted FALSE) ===")
for law1, law2, p in fn_errors[:15]:
    eq1 = parse_equation(law1)
    eq2 = parse_equation(law2)
    f1 = classify_form(eq1)
    f2 = classify_form(eq2)
    s1 = get_sig(eq1)
    s2 = get_sig(eq2)
    nv1 = len(tree_vars(eq1[0]) | tree_vars(eq1[1]))
    nv2 = len(tree_vars(eq2[0]) | tree_vars(eq2[1]))
    print(f"  p={p:.3f} form={f1}->{f2} sig={s1}->{s2} nvars={nv1}->{nv2}")
    print(f"    E1: {law1}")
    print(f"    E2: {law2}")

print("\n=== FALSE POSITIVES (should be FALSE, predicted TRUE) ===")
for law1, law2, p in fp_errors[:15]:
    eq1 = parse_equation(law1)
    eq2 = parse_equation(law2)
    f1 = classify_form(eq1)
    f2 = classify_form(eq2)
    s1 = get_sig(eq1)
    s2 = get_sig(eq2)
    nv1 = len(tree_vars(eq1[0]) | tree_vars(eq1[1]))
    nv2 = len(tree_vars(eq2[0]) | tree_vars(eq2[1]))
    print(f"  p={p:.3f} form={f1}->{f2} sig={s1}->{s2} nvars={nv1}->{nv2}")
    print(f"    E1: {law1}")
    print(f"    E2: {law2}")

# Analyze: what nvars patterns do the errors have?
from collections import Counter
fn_nvd = Counter()
fp_nvd = Counter()
for law1, law2, p in fn_errors:
    eq1 = parse_equation(law1)
    eq2 = parse_equation(law2)
    nv1 = len(tree_vars(eq1[0]) | tree_vars(eq1[1]))
    nv2 = len(tree_vars(eq2[0]) | tree_vars(eq2[1]))
    fn_nvd[nv1-nv2] += 1
for law1, law2, p in fp_errors:
    eq1 = parse_equation(law1)
    eq2 = parse_equation(law2)
    nv1 = len(tree_vars(eq1[0]) | tree_vars(eq1[1]))
    nv2 = len(tree_vars(eq2[0]) | tree_vars(eq2[1]))
    fp_nvd[nv1-nv2] += 1

print("\n=== NVD distribution of errors ===")
print(f"False negatives by nvd: {dict(sorted(fn_nvd.items()))}")
print(f"False positives by nvd: {dict(sorted(fp_nvd.items()))}")

# What fraction of hard triples does the BFS/counterexample approach decide?
decided_count = 0
for law1, law2, actual in generated_triples:
    p = predict_implication_v3(law1, law2)
    if p > 0.95 or p < 0.05:
        decided_count += 1
print(f"\nHigh-confidence decisions: {decided_count}/{len(generated_triples)}")

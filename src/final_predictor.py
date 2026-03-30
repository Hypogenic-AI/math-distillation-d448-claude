"""Final optimized predictor with enhanced BFS rewriting and counterexample search."""
import re
import random
import math
import itertools

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

def apply_subst(t, s):
    if isinstance(t, str): return s.get(t, t)
    return ('*', apply_subst(t[1], s), apply_subst(t[2], s))

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

def get_rewrites(term, rules, depth=0):
    if depth > 12 or tree_size(term) > 30:
        return set()
    results = set()
    for rl, rr in rules:
        s = {}
        if match_trees(rl, term, s):
            new_term = apply_subst(rr, s)
            if tree_size(new_term) <= 30:
                results.add(new_term)
    if not isinstance(term, str):
        for lt in get_rewrites(term[1], rules, depth+1):
            results.add(('*', lt, term[2]))
        for rt in get_rewrites(term[2], rules, depth+1):
            results.add(('*', term[1], rt))
    return results

def bfs_rewrite(start, rules, limit=500):
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

# Build comprehensive counterexample magma set
def build_magma_set():
    magmas = []
    # All 16 size-2 magmas
    for i in range(16):
        magmas.append([[(i>>(2*r+c))&1 for c in range(2)] for r in range(2)])
    # Linear magmas x*y = ax+by mod n
    for n in [2, 3, 5, 7]:
        for a in range(n):
            for b in range(n):
                magmas.append([[(a*r+b*c) % n for c in range(n)] for r in range(n)])
    # Quadratic x*y = ax+by+cxy mod n
    for n in [2, 3]:
        for a in range(n):
            for b in range(n):
                for c2 in range(n):
                    magmas.append([[(a*r+b*c+c2*r*c) % n for c in range(n)] for r in range(n)])
    # Special named magmas
    magmas.extend([
        [[r ^ c for c in range(4)] for r in range(4)],  # XOR
        [[r & c for c in range(4)] for r in range(4)],  # AND
        [[r | c for c in range(4)] for r in range(4)],  # OR
        [[(r+c) % 3 for c in range(3)] for r in range(3)],  # Z3 addition
        [[(r-c) % 3 for c in range(3)] for r in range(3)],  # Z3 subtraction
        [[max(r,c) for c in range(3)] for r in range(3)],  # MAX
        [[min(r,c) for c in range(3)] for r in range(3)],  # MIN
        [[(r+c) % 4 for c in range(4)] for r in range(4)],
        [[(r-c) % 4 for c in range(4)] for r in range(4)],
        [[(r*c) % 3 for c in range(3)] for r in range(3)],  # Z3 multiplication
        [[(r*c) % 5 for c in range(5)] for r in range(5)],
        [[r for _ in range(3)] for r in range(3)],  # left projection
        [[c for c in range(3)] for _ in range(3)],  # right projection
        [[(r+1)%3 for _ in range(3)] for r in range(3)],  # constant successor
        [[0,2,1],[2,1,0],[1,0,2]],  # Steiner triple
        [[0,1,2,3,4,5],[1,0,4,5,2,3],[2,5,0,4,3,1],[3,4,5,0,1,2],[4,3,1,2,5,0],[5,2,3,1,0,4]],  # S3
    ])
    # Commutative size 3
    for v in itertools.product(range(3), repeat=6):
        m = [[0]*3 for _ in range(3)]
        i = 0
        for r in range(3):
            for c in range(r, 3):
                m[r][c] = m[c][r] = v[i]
                i += 1
        magmas.append(m)
    return magmas

ALL_MAGMAS = build_magma_set()

def find_counterexample(eq1, eq2):
    for table in ALL_MAGMAS:
        try:
            if check_magma(eq1, table) and not check_magma(eq2, table):
                return True
        except:
            pass
    return False

# Stochastic hill-climbing counterexample search
def search_counterexample(eq1, eq2, sizes=[3, 4], restarts=10, steps=80):
    vars1 = sorted(tree_vars(eq1[0]) | tree_vars(eq1[1]))
    vars2 = sorted(tree_vars(eq2[0]) | tree_vars(eq2[1]))
    v1_idx = {v: i for i, v in enumerate(vars1)}
    v2_idx = {v: i for i, v in enumerate(vars2)}

    def ev(t, vals, vidx, table):
        if isinstance(t, str): return vals[vidx.get(t, 0)]
        return table[ev(t[1], vals, vidx, table)][ev(t[2], vals, vidx, table)]

    def score(table, sz):
        # Check eq1 satisfaction
        n1 = len(vars1)
        eq1_ok = True
        if sz ** n1 <= 256:
            for vals in itertools.product(range(sz), repeat=n1):
                if ev(eq1[0], vals, v1_idx, table) != ev(eq1[1], vals, v1_idx, table):
                    eq1_ok = False
                    break
        else:
            rng = random.Random(42)
            for _ in range(256):
                vals = tuple(rng.randint(0, sz-1) for _ in range(n1))
                if ev(eq1[0], vals, v1_idx, table) != ev(eq1[1], vals, v1_idx, table):
                    eq1_ok = False
                    break
        if not eq1_ok:
            return 1000  # bad: doesn't satisfy eq1

        # Check eq2 violation
        n2 = len(vars2)
        if sz ** n2 <= 256:
            for vals in itertools.product(range(sz), repeat=n2):
                if ev(eq2[0], vals, v2_idx, table) != ev(eq2[1], vals, v2_idx, table):
                    return 0  # found counterexample!
        else:
            rng = random.Random(42)
            for _ in range(256):
                vals = tuple(rng.randint(0, sz-1) for _ in range(n2))
                if ev(eq2[0], vals, v2_idx, table) != ev(eq2[1], vals, v2_idx, table):
                    return 0
        return 500  # satisfies both

    rng = random.Random(42)
    for sz in sizes:
        for _ in range(restarts):
            table = [[rng.randint(0, sz-1) for _ in range(sz)] for _ in range(sz)]
            cur = score(table, sz)
            if cur == 0: return True
            for _ in range(steps):
                r, c = rng.randint(0, sz-1), rng.randint(0, sz-1)
                old = table[r][c]
                table[r][c] = rng.randint(0, sz-1)
                new = score(table, sz)
                if new <= cur:
                    cur = new
                    if cur == 0: return True
                else:
                    table[r][c] = old
    return False

# Polynomial hashing counterexample
def hash_counterexample(eq1, eq2):
    vars_all = sorted(tree_vars(eq1[0]) | tree_vars(eq1[1]) | tree_vars(eq2[0]) | tree_vars(eq2[1]))
    for si in range(30):
        rng = random.Random(si + 777)
        for mod in [2147483647, 104729]:
            p = [rng.randint(1, mod-1) for _ in range(5)]
            v_map = {v: rng.randint(0, mod-1) for v in vars_all}
            for dual in [False, True]:
                def ev(n):
                    if isinstance(n, str): return v_map.get(n, 17)
                    ln, rn = (ev(n[2]), ev(n[1])) if dual else (ev(n[1]), ev(n[2]))
                    return (ln * p[0] + rn * p[1] + ln * rn * p[2] + (ln**2) * p[3] + (rn**2) * p[4]) % mod
                if ev(eq1[0]) == ev(eq1[1]):
                    if ev(eq2[0]) != ev(eq2[1]):
                        return True
    return False


def predict_implication_v3(law1_str, law2_str):
    """Final predictor. Returns probability that law1 implies law2."""
    law1_str = law1_str.replace('◇', '*')
    law2_str = law2_str.replace('◇', '*')

    try:
        eq1 = parse_equation(law1_str)
        eq2 = parse_equation(law2_str)
    except:
        return 0.37

    form1 = classify_form(eq1)
    form2 = classify_form(eq2)
    sig1 = get_sig(eq1)
    sig2 = get_sig(eq2)

    vars1 = tree_vars(eq1[0]) | tree_vars(eq1[1])
    vars2 = tree_vars(eq2[0]) | tree_vars(eq2[1])
    nvars1 = len(vars1)
    nvars2 = len(vars2)

    # === CERTAIN RULES ===
    if law1_str.replace(' ', '') == law2_str.replace(' ', ''):
        return 0.999
    if form2 == 'trivial': return 0.999
    if form1 == 'trivial': return 0.001
    if form1 == 'singleton': return 0.999
    if form1 == 'absorbing': return 0.999

    # Direct substitution
    s = {}
    if match_trees(eq1[0], eq2[0], s) and match_trees(eq1[1], eq2[1], s):
        return 0.999
    s = {}
    if match_trees(eq1[1], eq2[0], s) and match_trees(eq1[0], eq2[1], s):
        return 0.999

    # General never implies lhs_var/absorbing/singleton
    if form1 == 'general' and form2 in ('lhs_var', 'absorbing', 'singleton'):
        return 0.001

    # Signature direction
    if sig1[0] > 0 and sig2[0] == 0 and sig2[1] > 0:
        return 0.001
    if sig1[0] == 2 and sig2[0] < 2 and form2 != 'trivial':
        return 0.001
    if sig1[0] == 2 and sig2[0] == 1:
        return 0.001

    # === COMPUTATIONAL CHECKS ===

    # BFS rewriting
    rules = [(eq1[0], eq1[1]), (eq1[1], eq1[0])]
    try:
        reach_l = bfs_rewrite(eq2[0], rules, limit=500)
        reach_r = bfs_rewrite(eq2[1], rules, limit=500)
        if not reach_l.isdisjoint(reach_r):
            return 0.99

        # Also check: can we reach 'x' from any variable through rewriting?
        # If eq1 makes all elements equal, it implies everything
        for v in vars1:
            if v in rules[0][0] if is_var(rules[0][0]) else False:
                continue
            reached = bfs_rewrite(v, rules, limit=100)
            for w in vars1:
                if w != v and w in reached:
                    return 0.99
    except:
        pass

    # Hash-based counterexample
    try:
        if hash_counterexample(eq1, eq2):
            return 0.001
    except:
        pass

    # Finite magma counterexample search
    try:
        if find_counterexample(eq1, eq2):
            return 0.001
    except:
        pass

    # Hill-climbing counterexample
    try:
        if search_counterexample(eq1, eq2):
            return 0.001
    except:
        pass

    # === HEURISTIC RULES ===

    # 1-var and 2-var lhs_var
    if form1 == 'lhs_var' and nvars1 == 1 and nvars2 >= 2:
        return 0.01
    if form1 == 'lhs_var' and nvars1 == 2:
        if nvars2 >= 3: return 0.01
        if nvars2 == 2: return 0.02

    # Variable count based probability
    nvd = nvars1 - nvars2

    if form1 == 'lhs_var' and form2 == 'lhs_var':
        prob_map = {-4: 0.001, -3: 0.04, -2: 0.10, -1: 0.21, 0: 0.34, 1: 0.50, 2: 0.62, 3: 0.71, 4: 0.82}
    elif form1 == 'lhs_var' and form2 == 'general':
        prob_map = {-4: 0.001, -3: 0.04, -2: 0.11, -1: 0.22, 0: 0.36, 1: 0.51, 2: 0.65, 3: 0.74}
    elif form1 == 'general' and form2 == 'general':
        prob_map = {-4: 0.001, -3: 0.04, -2: 0.09, -1: 0.18, 0: 0.30, 1: 0.43, 2: 0.55, 3: 0.63, 4: 0.67}
    else:
        prob_map = {-4: 0.001, -3: 0.04, -2: 0.11, -1: 0.21, 0: 0.33, 1: 0.49, 2: 0.61, 3: 0.69, 4: 0.74}

    p = prob_map.get(nvd, 0.80 if nvd > 4 else 0.001 if nvd < -4 else 0.37)
    return p


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '/workspaces/math-distillation-d448-claude/code/equational_theories/scripts/predictor')

    # Test on short_test
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

    print("=== SHORT TEST ===")
    test_correct = 0
    ll_sum = 0.0
    for law1, law2, actual in short_test:
        p = predict_implication_v3(law1, law2)
        pred = p > 0.5
        is_correct = pred == actual
        test_correct += is_correct
        p_c = max(1e-9, min(1-1e-9, p))
        ll = math.log(p_c) if actual else math.log(1-p_c)
        ll_sum += ll
        status = "✓" if is_correct else "✗"
        print(f"  {status} p={p:.3f}, actual={actual}: {law1[:40]}...")
    print(f"Accuracy: {test_correct}/20 = {test_correct/20:.2f}")
    print(f"Avg LL: {ll_sum/20:.4f}")

    # Test on hard triples
    print("\n=== HARD TRIPLES ===")
    from hard_triples import generated_triples
    ht_correct = 0
    ht_ll = 0.0
    for law1, law2, actual in generated_triples:
        p = predict_implication_v3(law1, law2)
        pred = p > 0.5
        if pred == actual: ht_correct += 1
        p_c = max(1e-9, min(1-1e-9, p))
        ht_ll += math.log(p_c) if actual else math.log(1-p_c)
    n = len(generated_triples)
    print(f"Accuracy: {ht_correct}/{n} = {ht_correct/n:.4f}")
    print(f"Avg LL: {ht_ll/n:.4f}")

    # Large random sample
    print("\n=== RANDOM SAMPLE (10K) ===")
    import pandas as pd
    PRED_DIR = '/workspaces/math-distillation-d448-claude/code/equational_theories/scripts/predictor'
    with open(f"{PRED_DIR}/equations.txt") as f:
        equations = [line.strip() for line in f if line.strip()]
    df = pd.read_csv(f"{PRED_DIR}/raw_implications.csv", header=None)
    M = df.values

    random.seed(42)
    total = correct = 0
    ll_sum = 0.0
    for _ in range(10000):
        i = random.randint(0, len(equations)-1)
        j = random.randint(0, len(equations)-1)
        if i == j: continue
        total += 1
        actual = M[i][j] > 0
        p = predict_implication_v3(equations[i], equations[j])
        pred = p > 0.5
        if pred == actual: correct += 1
        p_c = max(1e-9, min(1-1e-9, p))
        ll_sum += math.log(p_c) if actual else math.log(1-p_c)
    print(f"Accuracy: {correct}/{total} = {correct/total:.4f}")
    print(f"Avg LL: {ll_sum/total:.4f}")

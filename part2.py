import re
from collections import deque

# Parse state string like 'q0q1fq2' into list of states and accept states
def parse_states(state_str):
    states = []
    accept = set()
    for match in re.finditer(r'(q\d+)(f?)', state_str):
        s = match.group(1)
        if s not in states:
            states.append(s)
        if match.group(2) == 'f':
            accept.add(s)
    return states, accept

# Parse a line defining an NPDA (states + transitions)
def parse_npda_line(line):
    parts = [p.strip() for p in line.strip().split(',')]
    states, accept = parse_states(parts[0])
    start = states[0]

    transitions = []
    for part in parts[1:]:
        idx = part.rfind('->')
        left = part[:idx]
        dest = part[idx+2:]

        m = re.match(r'(q\d+)-(.*)', left)
        src = m.group(1)
        trans_str = m.group(2)

        # each transition is input-pop-push, separated by |
        for t in trans_str.split('|'):
            segs = t.split('-')
            transitions.append((src, segs[0], segs[1], segs[2], dest))

    return set(states), accept, start, transitions

# Parse a line defining an NFA (states + transitions)
def parse_nfa_line(line):
    parts = [p.strip() for p in line.strip().split(',')]
    states, accept = parse_states(parts[0])
    start = states[0]

    transitions = []
    for part in parts[1:]:
        idx = part.rfind('->')
        left = part[:idx]
        dest = part[idx+2:]

        m = re.match(r'(q\d+)-(.*)', left)
        src = m.group(1)
        syms = m.group(2)

        # symbols separated by |
        for sym in syms.split('|'):
            transitions.append((src, sym.strip(), dest))

    return set(states), accept, start, transitions

# Build the intersection NPDA of M (NPDA) and N (NFA) using product construction
def build_intersection(m_states, m_accept, m_start, m_trans,
                       n_states, n_accept, n_start, n_trans):

    # get all stack symbols from M
    stack_alpha = {'z'}
    for (_, _, pop, push, _) in m_trans:
        stack_alpha.add(pop)
        if push != 'empty':
            stack_alpha.update(push)

    # build lookup tables for quick access
    pda_map = {}
    for (src, inp, pop, push, dest) in m_trans:
        pda_map.setdefault((src, inp), []).append((pop, push, dest))

    nfa_map = {}
    for (src, sym, dest) in n_trans:
        nfa_map.setdefault((src, sym), set()).add(dest)

    # map each (m_state, n_state) pair to a new state name
    pair_names = {}
    counter = [0]

    def name(ms, ns):
        p = (ms, ns)
        if p not in pair_names:
            pair_names[p] = f'q{counter[0]}'
            counter[0] += 1
        return pair_names[p]

    # BFS to find all reachable product states
    start_name = name(m_start, n_start)
    product_trans = []
    product_accept = set()
    seen_trans = set()

    def add_trans(sn, inp, pop, push, dn):
        t = (sn, inp, pop, push, dn)
        if t not in seen_trans:
            seen_trans.add(t)
            product_trans.append(t)

    visited = {(m_start, n_start)}
    queue = deque([(m_start, n_start)])

    while queue:
        ms, ns = queue.popleft()
        sn = name(ms, ns)

        if ms in m_accept and ns in n_accept:
            product_accept.add(sn)

        #these 3 cases were done by ai
        # case 1: both M and N read the same input symbol
        for inp_sym in ['a', 'b']:
            for (pop, push, m_dest) in pda_map.get((ms, inp_sym), []):
                for n_dest in nfa_map.get((ns, inp_sym), set()):
                    dn = name(m_dest, n_dest)
                    add_trans(sn, inp_sym, pop, push, dn)
                    if (m_dest, n_dest) not in visited:
                        visited.add((m_dest, n_dest))
                        queue.append((m_dest, n_dest))

        # case 2: M takes an epsilon transition, N stays
        for (pop, push, m_dest) in pda_map.get((ms, 'empty'), []):
            dn = name(m_dest, ns)
            add_trans(sn, 'empty', pop, push, dn)
            if (m_dest, ns) not in visited:
                visited.add((m_dest, ns))
                queue.append((m_dest, ns))

        # case 3: N takes an epsilon transition, M stays
        # pass through the stack by popping and pushing back each symbol
        for n_dest in nfa_map.get((ns, 'empty'), set()):
            for sym in stack_alpha:
                dn = name(ms, n_dest)
                add_trans(sn, 'empty', sym, sym, dn)
            if (ms, n_dest) not in visited:
                visited.add((ms, n_dest))
                queue.append((ms, n_dest))

    return set(pair_names.values()), product_accept, start_name, product_trans

# Format the NPDA into the required output string
def format_npda(states, accept, start, transitions):
    # start state first, then the rest sorted
    ordered = [start] + sorted(s for s in states if s != start)
    state_decl = ''.join(s + ('f' if s in accept else '') for s in ordered)

    # group transitions by (src, dest)
    groups = {}
    for (src, inp, pop, push, dest) in transitions:
        groups.setdefault((src, dest), []).append(f'{inp}-{pop}-{push}')

    parts = []
    for (src, dest), trans_list in groups.items():
        parts.append(f'{src}-{"|".join(trans_list)}->{dest}')

    return state_decl + ',' + ','.join(parts)

# Simulate the NPDA on an input string using BFS
# this was done by ai
def simulate(transitions, start, accept, input_str):
    # build transition lookup
    trans_map = {}
    for (src, inp, pop, push, dest) in transitions:
        trans_map.setdefault((src, inp), []).append((pop, push, dest))

    max_stack = min(2 * len(input_str) + 10, 50)

    # each config is (state, remaining_input, stack)
    initial = (start, input_str, 'z')
    queue = deque([initial])
    visited = {initial}

    while queue:
        state, rem, stack = queue.popleft()

        # accept if in accept state with no input left
        if state in accept and not rem:
            return "accept"

        if not stack:
            continue

        top = stack[-1]
        rest = stack[:-1]

        # try epsilon transitions, then transitions on next input symbol
        keys = [('empty', rem)]
        if rem:
            keys.append((rem[0], rem[1:]))

        for inp_key, new_rem in keys:
            for (pop, push, dest) in trans_map.get((state, inp_key), []):
                if pop != top:
                    continue
                if push == 'empty':
                    new_stack = rest
                else:
                    new_stack = rest + push[::-1]
                if len(new_stack) > max_stack:
                    continue
                config = (dest, new_rem, new_stack)
                if config not in visited:
                    visited.add(config)
                    queue.append(config)

    return "reject"


# --- Main ---

filename = input("Enter the filename: ")

try:
    with open(filename, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    exit()

# line 1 = NFA N, line 2 = NPDA M
n_states, n_accept, n_start, n_trans = parse_nfa_line(lines[0])
m_states, m_accept, m_start, m_trans = parse_npda_line(lines[1])

# build the intersection NPDA
int_states, int_accept, int_start, int_trans = build_intersection(
    m_states, m_accept, m_start, m_trans,
    n_states, n_accept, n_start, n_trans
)

# print the result
npda_str = format_npda(int_states, int_accept, int_start, int_trans)
print(f"\nIntersection NPDA:\n{npda_str}\n")

# test strings in a loop
while True:
    test_str = input("Enter a string to test (or 'quit' to exit): ").strip()
    if test_str.lower() == 'quit':
        break
    result = simulate(int_trans, int_start, int_accept, test_str)
    print(f"Result: {result}\n")

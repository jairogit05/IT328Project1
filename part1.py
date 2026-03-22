from collections import deque

filename = input("Enter the filename: ")
alphabet = ['a', 'b']
grammar = {}

try:
    with open(filename, 'r') as file:
        rules = [line.strip() for line in file if line.strip()]
        for rule in rules:
            if '->' in rule:
                lhs, rhs = rule.split('->')
                lhs = lhs.strip()
                productions = [p.strip() for p in rhs.split('|')]
                grammar[lhs] = productions
except FileNotFoundError:
    print(f"Error: The file '{filename}' was not found.")
    exit()

# The first LHS defined in the file is our start symbol
start_symbol = list(grammar.keys())[0]

def generate_npda(grammar, start):
    transitions_q0 = []

    # 1. Expand Non-Terminals
    for lhs, productions in grammar.items():
        for p in productions:
            # We use the literal 'empty' string for epsilon per your image
            transitions_q0.append(f"empty-{lhs}-{p}")

    # 2. Match Terminals
    for char in alphabet:
        transitions_q0.append(f"{char}-{char}-empty")
    
    # 3. Format strictly like the image example
    q0_to_q0 = f"q0-{ '|'.join(transitions_q0) }->q0"
    
    # Match the image's "Accept" transition: q0-empty-z-z->q1
    # This means: in q0, read nothing, pop 'z', push 'z', go to q1
    q0_to_q1 = "q0-empty-z-z->q1"

    return f"q0q1f,{q0_to_q1},{q0_to_q0}"

def run_simulation(grammar, start, input_str):
    # Initial stack has 'z' at bottom, start symbol on top
    initial = ('q0', input_str, ('z', start))
    queue = deque([initial])
    visited = {initial}

    while queue:
        state, rem_input, stack = queue.popleft()

        # Success: reached q1 and no input left
        if state == 'q1' and not rem_input:
            return "accept"

        if not stack:
            continue
            
        top = stack[-1]
        rest_of_stack = stack[:-1]

        # Scenario A: Transition to q1 (only if top of stack is 'z')
        if top == 'z':
            # Note: According to the image, we don't consume input to go to q1
            new_config = ('q1', rem_input, ('z',))
            if new_config not in visited:
                visited.add(new_config)
                queue.append(new_config)

        # Scenario B: Expansion (Non-Terminals)
        if top in grammar:
            for prod in grammar[top]:
                if prod == "empty":
                    new_stack = rest_of_stack
                else:
                    # Reverse production so first char is on top of stack
                    new_stack = rest_of_stack + tuple(prod)[::-1]
                
                new_config = (state, rem_input, new_stack)
                if new_config not in visited and len(new_stack) < 100: # Depth limit
                    visited.add(new_config)
                    queue.append(new_config)

        # Scenario C: Matching (Terminals)
        elif rem_input and top == rem_input[0]:
            new_config = (state, rem_input[1:], rest_of_stack)
            if new_config not in visited:
                visited.add(new_config)
                queue.append(new_config)

    return "reject"

# --- EXECUTION ---
npda_str = generate_npda(grammar, start_symbol)
print(f"\nGenerated NPDA:\n{npda_str}\n")

# Test loop
while True:
    test_str = input("Enter a string to test (or 'quit' to exit): ").strip()
    if test_str.lower() == 'quit': break
    
    result = run_simulation(grammar, start_symbol, test_str)
    print(f"Result: {result}\n")
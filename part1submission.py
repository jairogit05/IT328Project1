from collections import deque


alphabet = ['a', 'b']


def generate_npda(grammar, start):
    transitions_q0 = []

    for lhs, productions in grammar.items():
        for p in productions:
            # read nothing for non-terminals, pop lhs, push production
            transitions_q0.append(f"empty-{lhs}-{p}")

    for char in alphabet:
        # read terminal, pop terminal, push nothing
        transitions_q0.append(f"{char}-{char}-empty")
    
    # all transitions that keep us in q0 (non-terminal expansions and terminal matches)
    q0_to_q0 = f"q0-{ '|'.join(transitions_q0) }->q0"
    

    # if we're in q0 and top of stack is z move to accept state
    q0_to_q1 = "q0-empty-z-z->q1"

    return f"q0q1f,{q0_to_q1},{q0_to_q0}"

def run_simulation(grammar, start, input_str):
    
    # limit stack to prevent infinite loop
    MAX_STACK = 50

    initial = ('q0', input_str, ('z', start))
    queue = deque([initial])
    visited = {initial}


    # generative AI was used to help write some of the code below
    while queue:
        state, rem_input, stack = queue.popleft()

        if state == 'q1' and not rem_input:
            return "accept"

        if not stack:
            continue

        top = stack[-1]
        rest_of_stack = stack[:-1]

        # Case 1: Transition to q1 when 'z' is on top of the stack
        if top == 'z':
            new_config = ('q1', rem_input, ('z',))
            if new_config not in visited:
                visited.add(new_config)
                queue.append(new_config)

        # Case 2: Expand non-terminal symbols
        if top in grammar:
            for prod in grammar[top]:
                if prod == "empty":
                    new_stack = rest_of_stack
                else:
                    new_stack = rest_of_stack + tuple(prod)[::-1]

                if len(new_stack) > MAX_STACK:
                    continue

                new_config = (state, rem_input, new_stack)
                if new_config not in visited:
                    visited.add(new_config)
                    queue.append(new_config)

        # Case 3: Match terminals symbols
        elif rem_input and top == rem_input[0]:
            new_config = (state, rem_input[1:], rest_of_stack)
            if new_config not in visited:
                visited.add(new_config)
                queue.append(new_config)

    return "reject"

curr_file_name = None

while True:
    user_input = input(f"1 - Enter a file name (current file: {curr_file_name}) \n2 - Test a string \n3 - Quit\n")
    if user_input == '1':
        filename = input("Enter the filename: ")
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
            start_symbol = list(grammar.keys())[0]
            npda = generate_npda(grammar, start_symbol)
            curr_file_name = filename
            print(f"\nNPDA:\n{npda}\n")
            with open("npda.txt", "w") as f:
                f.write(npda)
        except FileNotFoundError:
            print(f"Error: The file '{filename}' was not found.")
            continue

    elif user_input == '2':
        input_string = input("Enter a string to test: \n").strip()

        result = run_simulation(grammar, start_symbol, input_string)
        print(f"Result: {result}\n")
        continue

    elif user_input == '3':
        print("Exiting the program.")
        break

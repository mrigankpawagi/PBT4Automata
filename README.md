# Property Based Testing for Finite Automata and Context-free Grammars

<p align=center>
    <img src="https://github.com/user-attachments/assets/c57f4822-eb3f-4e9e-9af3-7d22b927fbfe" />
</p>

This repository provides tools to construct finite automata and context-free grammars in Python and test them against a given rule for correctness. This testing is done using [Hypothesis](https://hypothesis.readthedocs.io/en/latest/index.html), a python library for property-based testing, which also provides a counter-example (often the smallest possible) in case of a mismatch. Note that this is not formal verification and cannot guarantee correctness. Nonetheless, this is a convenient (and usually sufficiently thorough) way to evaluate finite automata and context-free grammars.

### Dependencies

1. Hypothesis

```bash
pip install hypothesis
```

## Examples

### Deterministic Finite Automata

#### Testing a DFA against a rule

The following example tests a DFA that accepts all strings that contain the substring "010" or "100".

```python
from automaton import DFA
from tester import test

automata = DFA(
    states = ["q0", "q1", "q2", "q3", "q4", "q5"],
    alphabet = "01",
    transition_function = {
        ("q0", "0"): "q1",
        ("q0", "1"): "q4",
        ("q1", "0"): "q1",
        ("q1", "1"): "q2",
        ("q2", "0"): "q3",
        ("q2", "1"): "q4",
        ("q3", "0"): "q3",
        ("q3", "1"): "q3",
        ("q4", "0"): "q5",
        ("q4", "1"): "q4",
        ("q5", "0"): "q3",
        ("q5", "1"): "q2"
    },
    start_state = "q0",
    accept_states = ["q3"]
)

check = test(automata, "[01]*(010|100)[01]*")

if check == True:
    print("Success!")
else:
    print("Counterexample: " + check)
```

You can also pass a function of type `Callable[[str], bool]` to the `test` function instead of a regex.

#### Testing two DFAs for equivalence

```python
from automaton import DFA
from tester import test_equivalence

automata1 = DFA(
    ...
)

automata2 = DFA(
    ...
)

check = test_equivalence(automata1, automata2)

if check == True:
    print("Success!")
else:
    print("Counterexample: " + repr(check))
```

### Context-Free Grammars

#### Testing a CFG against a rule

The following example tests a CFG in Chomsky Normal Form that generates all non-empty strings of balanced parentheses.

```python
from grammar import CNF

cnf = CNF(
    terminals="()",
    nonterminals="SLRX",
    productions={
        "S": ["LX", "SS"],
        "L": ["("],
        "R": [")"],
        "X": ["SR", ")"]
    },
    start_symbol="S"
)

def check_balance(input_string: str) -> bool:
    if input_string == "":
        return False
    s = 0
    for c in input_string:
        if c == "(":
            s += 1
        elif c == ")":
            s -= 1
        if s < 0:
            return False
    return s == 0

check = cnf.test(check_balance)

if check == True:
    print("Success!")
else:
    print("Counterexample: " + check)
```

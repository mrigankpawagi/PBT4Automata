# pbt4automata

[![Tests](https://github.com/mrigankpawagi/pbt4automata/actions/workflows/tests.yml/badge.svg)](https://github.com/mrigankpawagi/pbt4automata/actions/workflows/tests.yml) ![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)

<p align=center>
    <img src="https://github.com/user-attachments/assets/c57f4822-eb3f-4e9e-9af3-7d22b927fbfe" />
</p>

`pbt4automata` provides tools to construct finite automata and context-free grammars in Python and validate their behavior with property-based tests powered by [Hypothesis](https://hypothesis.readthedocs.io/en/latest/index.html).

## Installation

```bash
pip install -e .
```

## Examples

### Deterministic Finite Automata

#### Testing a DFA against a rule

The following example tests a DFA that accepts all strings that contain the substring "010" or "100".

```python
from pbt4automata import DFA

automaton = DFA(
    states=["q0", "q1", "q2", "q3", "q4", "q5"],
    alphabet="01",
    transition_function={
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
        ("q5", "1"): "q2",
    },
    start_state="q0",
    accept_states=["q3"],
)

result = automaton.test("[01]*(010|100)[01]*")

if result is True:
    print("Success!")
else:
    print("Counterexample:", result)
```

You can also pass a function of type `Callable[[str], bool]` to `automaton.test(...)` instead of a regex.

#### Testing two DFAs for equivalence

```python
from pbt4automata import Automaton, DFA

automata1 = DFA(
    ...
)

automata2 = DFA(
    ...
)

result = Automaton.test_equivalence(automata1, automata2)

if result is True:
    print("Success!")
else:
    print("Counterexample:", repr(result))
```

### Context-Free Grammars

#### Testing a CFG against a rule

The following example tests a CFG in Chomsky Normal Form that generates all non-empty strings of balanced parentheses.

```python
from pbt4automata import CNF

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

result = cnf.test(check_balance)

if result is True:
    print("Success!")
else:
    print("Counterexample:", result)
```

#### Converting a general CFG to CNF

`Grammar` accepts any context-free grammar (productions of any length, including ε-productions). Call `to_cnf()` to obtain an equivalent `CNF` object, or use `Grammar.parse()` directly — it converts to CNF internally.

```python
from pbt4automata import Grammar

# Grammar for "a^n b^n" (n ≥ 1): S → aSb | ab
g = Grammar(
    terminals="ab",
    nonterminals="SAB",
    productions={
        "S": ["aSb", "ab"],
        "A": ["a"],
        "B": ["b"],
    },
    start_symbol="S",
)

cnf = g.to_cnf()   # returns a CNF instance with equivalent language

# Parse directly via Grammar (delegates to CNF internally)
print(g.parse("ab"))       # True
print(g.parse("aabb"))     # True
print(g.parse("aaabbb"))   # True
print(g.parse("aab"))      # False
```

You can then call `cnf.test(rule)` to property-test the converted grammar, or work with it like any other `CNF` object.

## Development

Install dev dependencies and run tests:

```bash
pip install -e ".[dev]"
pytest -v
```

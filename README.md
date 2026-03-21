# Property-Based Testing for Finite Automata and Context-Free Grammars

<p align=center>
    <img src="https://github.com/user-attachments/assets/c57f4822-eb3f-4e9e-9af3-7d22b927fbfe" />
</p>

**pbt4automata** provides tools to construct finite automata and context-free
grammars in Python and test them for correctness against a given specification.
Testing is powered by [Hypothesis](https://hypothesis.readthedocs.io/), which
generates inputs automatically and shrinks any counterexample to its smallest
possible form.  Note that this is *not* formal verification and cannot
guarantee correctness, but it is a convenient and usually thorough way to
validate formal-language constructs.

## Installation

```bash
pip install pbt4automata
```

To also install the development dependencies (pytest):

```bash
pip install "pbt4automata[dev]"
```

## Examples

### Deterministic Finite Automata

#### Testing a DFA against a specification

The following example tests a DFA that accepts all strings containing the
substring `"010"` or `"100"`.

```python
from pbt4automata import DFA

dfa = DFA(
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

result = dfa.test("[01]*(010|100)[01]*")

if result is True:
    print("Success!")
else:
    print("Counterexample:", result)
```

You can also pass a callable `(str) -> bool` instead of a regex string:

```python
result = dfa.test(lambda s: "010" in s or "100" in s)
```

#### Testing two DFAs for equivalence

```python
from pbt4automata import DFA, Automaton

dfa1 = DFA(...)
dfa2 = DFA(...)

result = Automaton.test_equivalence(dfa1, dfa2)

if result is True:
    print("The DFAs are equivalent.")
else:
    print("Counterexample:", repr(result))
```

### Context-Free Grammars

#### Testing a CNF grammar against a specification

The following example tests a grammar in Chomsky Normal Form (CNF) that
generates all non-empty balanced-parentheses strings.

```python
from pbt4automata import CNF

cnf = CNF(
    terminals="()",
    nonterminals="SLRX",
    productions={
        "S": ["LX", "SS"],
        "L": ["("],
        "R": [")"],
        "X": ["SR", ")"],
    },
    start_symbol="S",
)

def check_balance(s: str) -> bool:
    if not s:
        return False
    depth = 0
    for c in s:
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        if depth < 0:
            return False
    return depth == 0

result = cnf.test(check_balance)

if result is True:
    print("Success!")
else:
    print("Counterexample:", result)
```

## Exception Hierarchy

All exceptions raised by this library inherit from `PBT4AutomataError`:

```
PBT4AutomataError
├── AutomatonError
│   ├── InvalidStartStateError
│   ├── InvalidAcceptStatesError
│   ├── InvalidTransitionFunctionError
│   └── InvalidSymbolError
└── GrammarError
    ├── InvalidStartSymbolError
    └── InvalidProductionError
```

Import any exception directly from the package:

```python
from pbt4automata import InvalidStartStateError
```

## Development

```bash
git clone https://github.com/mrigankpawagi/PBT4Automata.git
cd PBT4Automata
pip install -e ".[dev]"
pytest
```


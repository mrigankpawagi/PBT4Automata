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

### Nondeterministic Finite Automata

#### Testing an NFA against a rule

NFAs support nondeterministic transitions (multiple possible next states for a given state and symbol) as well as epsilon (ε) transitions. The transition function maps `(state, symbol)` pairs to **sets** of states; use `None` as the symbol for ε-transitions. Unlike DFAs, the transition function may be partial.

The following example tests an NFA that accepts all strings over `{0, 1}` that end with the substring `"01"`.

```python
from pbt4automata import NFA

nfa = NFA(
    states=["q0", "q1", "q2"],
    alphabet="01",
    transition_function={
        ("q0", "0"): {"q0", "q1"},  # nondeterministically guess start of "01"
        ("q0", "1"): {"q0"},
        ("q1", "1"): {"q2"},
    },
    start_state="q0",
    accept_states=["q2"],
)

result = nfa.test("[01]*01")

if result is True:
    print("Success!")
else:
    print("Counterexample:", result)
```

You can also pass a function of type `Callable[[str], bool]` to `nfa.test(...)` instead of a regex.

#### NFA with epsilon transitions

```python
from pbt4automata import NFA

# Accepts "a" or "ab"
nfa = NFA(
    states=["q0", "q1", "q2", "q3"],
    alphabet="ab",
    transition_function={
        ("q0", "a"): {"q1"},
        ("q1", None): {"q2"},   # ε-transition: q1 is also effectively q2
        ("q1", "b"): {"q3"},
    },
    start_state="q0",
    accept_states=["q2", "q3"],
)
```

#### Testing an NFA for equivalence with another automaton

`Automaton.test_equivalence` works with any mix of `DFA` and `NFA` objects sharing the same alphabet.

```python
from pbt4automata import Automaton, DFA, NFA

nfa = NFA(...)
dfa = DFA(...)

result = Automaton.test_equivalence(nfa, dfa)

if result is True:
    print("Success!")
else:
    print("Counterexample:", repr(result))
```

### Context-Free Grammars

#### Testing a CFG against a rule

The following example tests a CFG that generates all non-empty strings of balanced parentheses.

```python
from pbt4automata import Grammar

grammar = Grammar(
    terminals="()",
    nonterminals="S",
    productions={
        "S": ["(S)", "SS", "()"],
    },
    start_symbol="S",
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

result = grammar.test(check_balance)

if result is True:
    print("Success!")
else:
    print("Counterexample:", result)
```

You can also pass a function of type `Callable[[str], bool]` to `grammar.test(...)`.

#### Parsing strings

```python
from pbt4automata import Grammar

# Grammar for "a^n b^n" (n ≥ 1): S → aSb | ab
grammar = Grammar(
    terminals="ab",
    nonterminals="S",
    productions={
        "S": ["aSb", "ab"],
    },
    start_symbol="S",
)

print(grammar.parse("ab"))       # True
print(grammar.parse("aabb"))     # True
print(grammar.parse("aaabbb"))   # True
print(grammar.parse("aab"))      # False
```

## Development

Install dev dependencies and run tests:

```bash
pip install -e ".[dev]"
pytest -v
```

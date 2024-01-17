# Property Based Testing for Automata

### Dependencies

1. Hypothesis

```bash
pip install hypothesis
```

## Examples

### Deterministic Finite Automata

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

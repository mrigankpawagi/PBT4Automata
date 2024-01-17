from automaton import Automaton
from hypothesis import given, strategies as st, settings
import re


def test(automaton: Automaton, pattern: str):
    """
    Uses hypothesis to test the automaton against the given pattern (regex)
    """
    alphabet = automaton.alphabet
    num_states = len(automaton.states)
    # We scale this by 5 but this can be changed
    
    counter_example = None
    
    @given(st.text(alphabet=alphabet, max_size=num_states * 5))
    @settings(max_examples=1000)
    def run(input_string):
        # Run the automaton on the input string
        result = automaton.run(input_string)
        
        # Check if the result matches the result from the regex matching
        assert result == bool(re.fullmatch(pattern, input_string)), input_string

    try:
        run()
    except AssertionError as e:
        # If the assertion fails, we return a counter example
        counter_example = e.args[0].split("\n")[0]
        return counter_example
        
    return True

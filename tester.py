from automaton import Automaton
from hypothesis import given, strategies as st, settings
import re
from typing import Callable

STATE_SCALE_FACTOR = 5 # length of the longest string to test as a multiple of the number of states


def test(automaton: Automaton, pattern: str | Callable[[str], bool]):
    """
    Uses hypothesis to test the automaton against the 
    given pattern (regex or function)
    
    The regex must be a string, and the function must be be of
    type Callable[[str], bool]
    """
    alphabet = automaton.alphabet
    num_states = len(automaton.states)
    
    if isinstance(pattern, str):
        checker = lambda s: bool(re.fullmatch(pattern, s))
    else:
        checker = pattern
    
    counter_example = None
    
    @given(st.text(alphabet=alphabet, max_size=num_states * STATE_SCALE_FACTOR))
    @settings(max_examples=1000)
    def run(input_string):
        # Run the automaton on the input string
        result = automaton.run(input_string)
        
        # Check if the result matches the result from the regex matching
        assert result == checker(input_string), input_string

    try:
        run()
    except AssertionError as e:
        # If the assertion fails, we return a counter example
        counter_example = e.args[0].split("\n")[0]
        return counter_example
        
    return True


def test_equivalence(automaton1: Automaton, automaton2: Automaton):
    """
    Tests if two automata are equivalent. The automata must have the same alphabet
    """
    assert automaton1.alphabet == automaton2.alphabet, "Alphabets are not the same"
    
    alphabet = automaton1.alphabet
    num_states = max(len(automaton1.states), len(automaton2.states))
    
    @given(st.text(alphabet=alphabet, max_size=num_states * STATE_SCALE_FACTOR))
    @settings(max_examples=1000)
    def run(input_string):
        # Run the automaton on the input string
        result1 = automaton1.run(input_string)
        result2 = automaton2.run(input_string)
        
        # Check if the result matches the result from the regex matching
        assert result1 == result2, input_string

    try:
        run()
    except AssertionError as e:
        # If the assertion fails, we return a counter example
        counter_example = e.args[0].split("\n")[0]
        return counter_example
    
    return True

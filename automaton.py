from __future__ import annotations
from abc import ABC
from hypothesis import given, strategies as st, settings
import re
from typing import Callable


class Automaton(ABC):
    TEST_SCALE_FACTOR = 5 # length of the longest string to test as a multiple of the number of states
    
    def test(self, pattern: str | Callable[[str], bool]):
        """
        Uses hypothesis to test the automaton against the 
        given pattern (regex or function)
        
        The regex must be a string, and the function must be be of
        type Callable[[str], bool]
        """
        alphabet = self.alphabet
        num_states = len(self.states)
        
        if isinstance(pattern, str):
            checker = lambda s: bool(re.fullmatch(pattern, s))
        else:
            checker = pattern
        
        counter_example = None
        
        @given(st.text(alphabet=alphabet, max_size=num_states * Automaton.TEST_SCALE_FACTOR))
        @settings(max_examples=1000)
        def run(input_string):
            # Run the automaton on the input string
            result = self.run(input_string)
            
            # Check if the result matches the result from the regex matching
            assert result == checker(input_string), input_string

        try:
            run()
        except AssertionError as e:
            # If the assertion fails, we return a counter example
            counter_example = e.args[0].split("\n")[0]
            return counter_example
            
        return True

    @staticmethod
    def test_equivalence(automaton1: Automaton, automaton2: Automaton):
        """
        Tests if two automata are equivalent. The automata must have the same alphabet
        """
        assert automaton1.alphabet == automaton2.alphabet, "Alphabets are not the same"
        
        alphabet = automaton1.alphabet
        num_states = max(len(automaton1.states), len(automaton2.states))
        
        @given(st.text(alphabet=alphabet, max_size=num_states * Automaton.TEST_SCALE_FACTOR))
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


class DFA(Automaton):
    """
    A Deterministic Finite Automaton (DFA)
    """
    
    def __init__(self, states: list, alphabet: list, transition_function: dict, start_state, accept_states: list):
        """
        Initialize the DFA with the given parameters
        
        states: sequence of labels for the states
        alphabet: sequence of symbols in the alphabet
        transition_function: dictionary of transitions of the form {(state, symbol): state}
        start_state: label of the start state
        accept_states: sequence of labels of accept states
        """
        # Start state must not be None
        if start_state is None:
            raise Exception("Start state cannot be None")
        
        # Check if start state is in the list of states
        if start_state not in states:
            raise Exception("Start state is not in the list of states")
        
        # Check if all accept states are in the list of states
        if not all(state in states for state in accept_states):
            raise Exception("Accept states are not in the list of states")
        
        # Check if the transition function is valid
        for state in states:
            for symbol in alphabet:
                if (state, symbol) not in transition_function:
                    raise Exception("Transition function is not valid")
        for state in transition_function.values():
            if state not in states:
                raise Exception("Transition function is not valid")        
        
        self.states = states
        self.alphabet = alphabet
        self.transition_function = transition_function
        self.start_state = start_state
        self.accept_states = accept_states
        
    def run(self, input_string: str) -> bool:
        """
        Run the DFA on the given input string
        
        input_string: string of symbols in the alphabet
        """
        # Start at the start state
        current_state = self.start_state
        
        # Iterate through the input string
        for symbol in input_string:
            # Check if the symbol is in the alphabet
            if symbol not in self.alphabet:
                raise Exception("Symbol is not in the alphabet")
            
            # Get the next state
            current_state = self.transition_function[(current_state, symbol)]
        
        # Check if the final state is an accept state
        return current_state in self.accept_states

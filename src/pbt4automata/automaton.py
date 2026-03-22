from __future__ import annotations

from abc import ABC, abstractmethod
import re
from typing import Callable, Sequence, TypeAlias

from hypothesis import given, settings, strategies as st

from .exceptions import (
    AlphabetMismatchError,
    InvalidAcceptStatesError,
    InvalidStartStateError,
    InvalidSymbolError,
    InvalidTransitionFunctionError,
)

State: TypeAlias = str
Symbol: TypeAlias = str
TransitionFunction: TypeAlias = dict[tuple[State, Symbol], State]
NFA_TransitionFunction: TypeAlias = dict[tuple[State, Symbol | None], set[State]]
Rule: TypeAlias = str | Callable[[str], bool]
TestResult: TypeAlias = bool | str


class Automaton(ABC):
    TEST_SCALE_FACTOR = 5

    @property
    @abstractmethod
    def alphabet(self) -> Sequence[Symbol]:
        """Alphabet symbols supported by the automaton."""

    @property
    @abstractmethod
    def states(self) -> Sequence[State]:
        """States available in the automaton."""

    @abstractmethod
    def run(self, input_string: str) -> bool:
        """Run the automaton on an input string."""

    def test(self, pattern: Rule) -> TestResult:
        alphabet = self.alphabet
        num_states = len(self.states)
        checker: Callable[[str], bool]
        if isinstance(pattern, str):
            checker = lambda s: bool(re.fullmatch(pattern, s))
        else:
            checker = pattern

        @given(st.text(alphabet=alphabet, max_size=num_states * Automaton.TEST_SCALE_FACTOR))
        @settings(max_examples=1000)
        def run_case(input_string: str) -> None:
            assert self.run(input_string) == checker(input_string), input_string

        try:
            run_case()
        except AssertionError as err:
            return str(err.args[0]).split("\n")[0]
        return True

    @staticmethod
    def test_equivalence(automaton1: Automaton, automaton2: Automaton) -> TestResult:
        if tuple(automaton1.alphabet) != tuple(automaton2.alphabet):
            raise AlphabetMismatchError("Alphabets are not the same")

        alphabet = automaton1.alphabet
        num_states = max(len(automaton1.states), len(automaton2.states))

        @given(st.text(alphabet=alphabet, max_size=num_states * Automaton.TEST_SCALE_FACTOR))
        @settings(max_examples=1000)
        def run_case(input_string: str) -> None:
            assert automaton1.run(input_string) == automaton2.run(input_string), input_string

        try:
            run_case()
        except AssertionError as err:
            return str(err.args[0]).split("\n")[0]
        return True


class DFA(Automaton):
    def __init__(
        self,
        states: Sequence[State],
        alphabet: Sequence[Symbol] | str,
        transition_function: TransitionFunction,
        start_state: State | None,
        accept_states: Sequence[State],
    ) -> None:
        normalized_states = tuple(states)
        normalized_alphabet = tuple(alphabet)
        normalized_accept_states = tuple(accept_states)

        if start_state is None:
            raise InvalidStartStateError("Start state cannot be None")
        if start_state not in normalized_states:
            raise InvalidStartStateError("Start state is not in the list of states")
        if not all(state in normalized_states for state in normalized_accept_states):
            raise InvalidAcceptStatesError("Accept states are not in the list of states")

        for state in normalized_states:
            for symbol in normalized_alphabet:
                if (state, symbol) not in transition_function:
                    raise InvalidTransitionFunctionError("Transition function is not valid")
        for state in transition_function.values():
            if state not in normalized_states:
                raise InvalidTransitionFunctionError("Transition function is not valid")

        self._states = normalized_states
        self._alphabet = normalized_alphabet
        self.transition_function = transition_function
        self.start_state = start_state
        self.accept_states = normalized_accept_states

    @property
    def states(self) -> Sequence[State]:
        return self._states

    @property
    def alphabet(self) -> Sequence[Symbol]:
        return self._alphabet

    def run(self, input_string: str) -> bool:
        current_state = self.start_state
        for symbol in input_string:
            if symbol not in self.alphabet:
                raise InvalidSymbolError("Symbol is not in the alphabet")
            current_state = self.transition_function[(current_state, symbol)]
        return current_state in self.accept_states


class NFA(Automaton):
    def __init__(
        self,
        states: Sequence[State],
        alphabet: Sequence[Symbol] | str,
        transition_function: NFA_TransitionFunction,
        start_state: State | None,
        accept_states: Sequence[State],
    ) -> None:
        normalized_states = tuple(states)
        normalized_alphabet = tuple(alphabet)
        normalized_accept_states = tuple(accept_states)

        if start_state is None:
            raise InvalidStartStateError("Start state cannot be None")
        if start_state not in normalized_states:
            raise InvalidStartStateError("Start state is not in the list of states")
        if not all(state in normalized_states for state in normalized_accept_states):
            raise InvalidAcceptStatesError("Accept states are not in the list of states")

        for (state, symbol), next_states in transition_function.items():
            if state not in normalized_states:
                raise InvalidTransitionFunctionError("Transition function is not valid")
            if symbol is not None and symbol not in normalized_alphabet:
                raise InvalidTransitionFunctionError("Transition function is not valid")
            if not all(s in normalized_states for s in next_states):
                raise InvalidTransitionFunctionError("Transition function is not valid")

        self._states = normalized_states
        self._alphabet = normalized_alphabet
        self.transition_function = transition_function
        self.start_state = start_state
        self.accept_states = normalized_accept_states

    @property
    def states(self) -> Sequence[State]:
        return self._states

    @property
    def alphabet(self) -> Sequence[Symbol]:
        return self._alphabet

    def _epsilon_closure(self, states: frozenset[State]) -> frozenset[State]:
        """Compute the epsilon closure of a set of states."""
        closure: set[State] = set(states)
        stack = list(states)
        while stack:
            state = stack.pop()
            for next_state in self.transition_function.get((state, None), set()):
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)
        return frozenset(closure)

    def run(self, input_string: str) -> bool:
        current_states = self._epsilon_closure(frozenset([self.start_state]))
        for symbol in input_string:
            if symbol not in self.alphabet:
                raise InvalidSymbolError("Symbol is not in the alphabet")
            next_states: set[State] = set()
            for state in current_states:
                next_states.update(self.transition_function.get((state, symbol), set()))
            current_states = self._epsilon_closure(frozenset(next_states))
        return bool(current_states & set(self.accept_states))

"""Finite automaton definitions and property-based testing utilities."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

from pbt4automata.exceptions import (
    InvalidAcceptStatesError,
    InvalidStartStateError,
    InvalidSymbolError,
    InvalidTransitionFunctionError,
)

__all__ = ["Automaton", "DFA"]


class Automaton(ABC):
    """Abstract base class for finite automata."""

    #: Length of the longest string to test as a multiple of the number of states.
    TEST_SCALE_FACTOR: int = 5

    @abstractmethod
    def run(self, input_string: str) -> bool:
        """Run the automaton on *input_string* and return whether it is accepted."""

    def test(self, pattern: str | Callable[[str], bool]) -> bool | str:
        """Test the automaton against *pattern* using property-based testing.

        Generates up to 1 000 strings from the automaton's alphabet (up to
        length ``num_states × TEST_SCALE_FACTOR``) and checks that the
        automaton agrees with *pattern* on every one of them.

        Args:
            pattern: Either a regular-expression string (matched with
                :func:`re.fullmatch`) or a callable ``(str) -> bool`` that
                serves as the reference oracle.

        Returns:
            ``True`` if no counterexample was found, or the counterexample
            string (often the shortest one) if the automaton disagrees with
            *pattern*.
        """
        alphabet = self.alphabet
        num_states = len(self.states)

        if isinstance(pattern, str):
            checker: Callable[[str], bool] = lambda s: bool(re.fullmatch(pattern, s))
        else:
            checker = pattern

        @given(st.text(alphabet=alphabet, max_size=num_states * Automaton.TEST_SCALE_FACTOR))
        @settings(max_examples=1000)
        def _run(input_string: str) -> None:
            assert self.run(input_string) == checker(input_string), input_string

        try:
            _run()
        except AssertionError as exc:
            return exc.args[0].split("\n")[0]

        return True

    @staticmethod
    def test_equivalence(
        automaton1: Automaton,
        automaton2: Automaton,
    ) -> bool | str:
        """Test whether *automaton1* and *automaton2* accept the same language.

        Both automata must share the same alphabet.

        Args:
            automaton1: The first automaton.
            automaton2: The second automaton.

        Returns:
            ``True`` if no counterexample was found, or the counterexample
            string if the two automata disagree on some input.

        Raises:
            AssertionError: If the alphabets of the two automata differ.
        """
        assert automaton1.alphabet == automaton2.alphabet, "Alphabets are not the same"

        alphabet = automaton1.alphabet
        num_states = max(len(automaton1.states), len(automaton2.states))

        @given(st.text(alphabet=alphabet, max_size=num_states * Automaton.TEST_SCALE_FACTOR))
        @settings(max_examples=1000)
        def _run(input_string: str) -> None:
            assert (
                automaton1.run(input_string) == automaton2.run(input_string)
            ), input_string

        try:
            _run()
        except AssertionError as exc:
            return exc.args[0].split("\n")[0]

        return True


class DFA(Automaton):
    """A Deterministic Finite Automaton (DFA).

    Example:
        A two-state DFA over ``{a, b}`` that accepts all strings ending with
        ``'a'``::

            dfa = DFA(
                states=["q0", "q1"],
                alphabet="ab",
                transition_function={
                    ("q0", "a"): "q1",
                    ("q0", "b"): "q0",
                    ("q1", "a"): "q1",
                    ("q1", "b"): "q0",
                },
                start_state="q0",
                accept_states=["q1"],
            )
            dfa.test("[ab]*a")  # returns True
    """

    def __init__(
        self,
        states: Sequence[Any],
        alphabet: Sequence[str] | str,
        transition_function: dict[tuple[Any, str], Any],
        start_state: Any,
        accept_states: Sequence[Any],
    ) -> None:
        """Initialise a DFA.

        Args:
            states: Sequence of state labels (any hashable type).
            alphabet: Sequence of single-character symbols, or a string whose
                characters form the alphabet.
            transition_function: Complete mapping
                ``{(state, symbol): next_state}`` covering every
                ``(state, symbol)`` pair.
            start_state: Label of the initial state.  Must be present in
                *states*.
            accept_states: Sequence of accepting state labels.  All must be
                present in *states*.

        Raises:
            InvalidStartStateError: If *start_state* is ``None`` or not in
                *states*.
            InvalidAcceptStatesError: If any element of *accept_states* is not
                in *states*.
            InvalidTransitionFunctionError: If *transition_function* is
                incomplete or maps to a state not in *states*.
        """
        if start_state is None:
            raise InvalidStartStateError("Start state cannot be None")
        if start_state not in states:
            raise InvalidStartStateError("Start state is not in the list of states")
        if not all(state in states for state in accept_states):
            raise InvalidAcceptStatesError("Accept states are not in the list of states")

        for state in states:
            for symbol in alphabet:
                if (state, symbol) not in transition_function:
                    raise InvalidTransitionFunctionError("Transition function is not valid")
        for state in transition_function.values():
            if state not in states:
                raise InvalidTransitionFunctionError("Transition function is not valid")

        self.states: list[Any] = list(states)
        self.alphabet: Sequence[str] | str = alphabet
        self.transition_function = transition_function
        self.start_state = start_state
        self.accept_states: list[Any] = list(accept_states)

    def run(self, input_string: str) -> bool:
        """Run the DFA on *input_string*.

        Args:
            input_string: A string whose characters must all belong to the
                alphabet.

        Returns:
            ``True`` if *input_string* is accepted, ``False`` otherwise.

        Raises:
            InvalidSymbolError: If *input_string* contains a character not in
                the alphabet.
        """
        current_state = self.start_state
        for symbol in input_string:
            if symbol not in self.alphabet:
                raise InvalidSymbolError("Symbol is not in the alphabet")
            current_state = self.transition_function[(current_state, symbol)]
        return current_state in self.accept_states

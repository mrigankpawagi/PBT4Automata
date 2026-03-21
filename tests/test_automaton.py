"""Tests for the DFA and Automaton classes."""

import re
import pytest
from pbt4automata import DFA, Automaton
from pbt4automata.exceptions import (
    InvalidAcceptStatesError,
    InvalidStartStateError,
    InvalidSymbolError,
    InvalidTransitionFunctionError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ends_with_a() -> DFA:
    """
    DFA over alphabet {a, b} that accepts exactly the non-empty strings whose
    last character is 'a'.  Language = [ab]*a.

    States
    ------
    q0 : start, rejecting – "last symbol was not 'a' (or no input yet)"
    q1 : accepting         – "last symbol was 'a'"

    Transitions (traced manually)
    ------------------------------
    q0 --a--> q1   q0 --b--> q0
    q1 --a--> q1   q1 --b--> q0
    """
    return DFA(
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


def _make_accepts_all() -> DFA:
    """Single-state DFA that accepts every string over {a, b}."""
    return DFA(
        states=["q0"],
        alphabet="ab",
        transition_function={("q0", "a"): "q0", ("q0", "b"): "q0"},
        start_state="q0",
        accept_states=["q0"],
    )


# ---------------------------------------------------------------------------
# 1. DFA construction – validation tests
# ---------------------------------------------------------------------------

class TestDFAConstruction:
    def test_none_start_state_raises(self):
        with pytest.raises(InvalidStartStateError, match="Start state cannot be None"):
            DFA(
                states=["q0"],
                alphabet="a",
                transition_function={("q0", "a"): "q0"},
                start_state=None,
                accept_states=[],
            )

    def test_start_state_not_in_states_raises(self):
        with pytest.raises(InvalidStartStateError, match="Start state is not in the list of states"):
            DFA(
                states=["q0"],
                alphabet="a",
                transition_function={("q0", "a"): "q0"},
                start_state="q99",
                accept_states=[],
            )

    def test_accept_state_not_in_states_raises(self):
        with pytest.raises(InvalidAcceptStatesError, match="Accept states are not in the list of states"):
            DFA(
                states=["q0"],
                alphabet="a",
                transition_function={("q0", "a"): "q0"},
                start_state="q0",
                accept_states=["q99"],
            )

    def test_incomplete_transition_function_raises(self):
        # Missing transitions for q1
        with pytest.raises(InvalidTransitionFunctionError, match="Transition function is not valid"):
            DFA(
                states=["q0", "q1"],
                alphabet="ab",
                transition_function={("q0", "a"): "q1", ("q0", "b"): "q0"},
                start_state="q0",
                accept_states=[],
            )

    def test_transition_to_unknown_state_raises(self):
        with pytest.raises(InvalidTransitionFunctionError, match="Transition function is not valid"):
            DFA(
                states=["q0"],
                alphabet="a",
                transition_function={("q0", "a"): "q99"},
                start_state="q0",
                accept_states=[],
            )

    def test_valid_dfa_constructs_without_error(self):
        dfa = _make_ends_with_a()
        assert dfa is not None


# ---------------------------------------------------------------------------
# 2. DFA.run() – deterministic unit tests
#    Expected values derived by manually tracing each input through the DFA.
# ---------------------------------------------------------------------------

class TestDFARun:
    """
    DFA under test: _make_ends_with_a()  (accepts [ab]*a)

    Trace examples
    --------------
    ""      : start at q0 → q0 not in accept_states → False
    "a"     : q0 --a--> q1  → True
    "b"     : q0 --b--> q0  → False
    "ba"    : q0 --b--> q0 --a--> q1  → True
    "ab"    : q0 --a--> q1 --b--> q0  → False
    "aa"    : q0 --a--> q1 --a--> q1  → True
    "bba"   : q0 --b--> q0 --b--> q0 --a--> q1  → True
    "bab"   : q0 --b--> q0 --a--> q1 --b--> q0  → False
    """

    @pytest.fixture(autouse=True)
    def dfa(self):
        self.dfa = _make_ends_with_a()

    def test_empty_string_rejected(self):
        assert self.dfa.run("") is False

    def test_single_a_accepted(self):
        assert self.dfa.run("a") is True

    def test_single_b_rejected(self):
        assert self.dfa.run("b") is False

    def test_ba_accepted(self):
        assert self.dfa.run("ba") is True

    def test_ab_rejected(self):
        assert self.dfa.run("ab") is False

    def test_aa_accepted(self):
        assert self.dfa.run("aa") is True

    def test_bba_accepted(self):
        assert self.dfa.run("bba") is True

    def test_bab_rejected(self):
        assert self.dfa.run("bab") is False

    def test_symbol_not_in_alphabet_raises(self):
        with pytest.raises(InvalidSymbolError, match="Symbol is not in the alphabet"):
            self.dfa.run("c")


# ---------------------------------------------------------------------------
# 3. DFA.test() – property-based testing via Hypothesis
# ---------------------------------------------------------------------------

class TestDFATest:
    def test_correct_dfa_passes(self):
        """
        The 'ends with a' DFA correctly implements [ab]*a, so test() must
        return True (Hypothesis found no counterexample in 1000 trials).
        """
        dfa = _make_ends_with_a()
        assert dfa.test("[ab]*a") is True

    def test_incorrect_dfa_returns_counterexample(self):
        """
        This DFA marks *both* q0 and q1 as accepting, so it accepts every
        string including the empty string and strings ending with 'b'.
        test() must return a counterexample (not True).

        We validate the counterexample by checking that it actually exposes
        the bug: the DFA and the regex [ab]*a disagree on that string.
        """
        buggy_dfa = DFA(
            states=["q0", "q1"],
            alphabet="ab",
            transition_function={
                ("q0", "a"): "q1",
                ("q0", "b"): "q0",
                ("q1", "a"): "q1",
                ("q1", "b"): "q0",
            },
            start_state="q0",
            accept_states=["q0", "q1"],  # Bug: q0 should not be an accept state
        )
        result = buggy_dfa.test("[ab]*a")

        assert result is not True
        assert isinstance(result, str)

        # The counterexample must actually witness the mismatch
        dfa_verdict = buggy_dfa.run(result)
        regex_verdict = bool(re.fullmatch("[ab]*a", result))
        assert dfa_verdict != regex_verdict

    def test_accepts_all_dfa_passes_accepts_all_regex(self):
        """Single-state, all-accepting DFA correctly implements [ab]*."""
        dfa = _make_accepts_all()
        assert dfa.test("[ab]*") is True

    def test_correct_dfa_with_callable_passes(self):
        """DFA.test() also accepts a callable instead of a regex string."""
        dfa = _make_ends_with_a()
        rule = lambda s: len(s) > 0 and s[-1] == "a"
        assert dfa.test(rule) is True


# ---------------------------------------------------------------------------
# 4. Automaton.test_equivalence()
# ---------------------------------------------------------------------------

class TestDFAEquivalence:
    def test_equivalent_dfas_return_true(self):
        """
        dfa1: minimal 2-state DFA for [ab]*a
        dfa2: non-minimal 4-state DFA for the same language

        dfa2 states
        -----------
        s0 : start, reject – "last symbol was not 'a' and not 'b' after a non-a"
             (equivalent to q0)
        s1 : accept – "last symbol was 'a'"  (equivalent to q1)
        s2 : reject – "last symbol was 'b' from a reject-state" (same as q0)
        s3 : accept – "last symbol was 'a' from s2"  (equivalent to q1)

        Both DFAs accept exactly the strings ending with 'a'.
        """
        dfa1 = _make_ends_with_a()
        dfa2 = DFA(
            states=["s0", "s1", "s2", "s3"],
            alphabet="ab",
            transition_function={
                ("s0", "a"): "s1",
                ("s0", "b"): "s2",
                ("s1", "a"): "s1",
                ("s1", "b"): "s2",
                ("s2", "a"): "s3",
                ("s2", "b"): "s2",
                ("s3", "a"): "s1",
                ("s3", "b"): "s2",
            },
            start_state="s0",
            accept_states=["s1", "s3"],
        )
        assert Automaton.test_equivalence(dfa1, dfa2) is True

    def test_non_equivalent_dfas_return_counterexample(self):
        """
        dfa1 accepts [ab]*a (strings ending with 'a').
        dfa2 accepts [ab]*  (all strings, because q0 is also an accept state).

        Any string that does NOT end with 'a' — e.g. "" or "b" — is accepted
        by dfa2 but rejected by dfa1, so test_equivalence must find one.
        """
        dfa1 = _make_ends_with_a()
        dfa2 = DFA(
            states=["q0", "q1"],
            alphabet="ab",
            transition_function={
                ("q0", "a"): "q1",
                ("q0", "b"): "q0",
                ("q1", "a"): "q1",
                ("q1", "b"): "q0",
            },
            start_state="q0",
            accept_states=["q0", "q1"],
        )
        result = Automaton.test_equivalence(dfa1, dfa2)

        assert result is not True
        assert isinstance(result, str)

        # The counterexample must actually witness the difference
        assert dfa1.run(result) != dfa2.run(result)

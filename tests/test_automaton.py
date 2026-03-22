"""Tests for automaton.py (DFA and Automaton classes)."""

import re
import pytest
from pbt4automata import (
    AlphabetMismatchError,
    Automaton,
    DFA,
    InvalidAcceptStatesError,
    InvalidStartStateError,
    InvalidSymbolError,
    InvalidTransitionFunctionError,
    NFA,
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

    def test_mismatched_alphabet_raises(self):
        dfa1 = DFA(
            states=["q0"],
            alphabet="ab",
            transition_function={("q0", "a"): "q0", ("q0", "b"): "q0"},
            start_state="q0",
            accept_states=["q0"],
        )
        dfa2 = DFA(
            states=["q0"],
            alphabet="01",
            transition_function={("q0", "0"): "q0", ("q0", "1"): "q0"},
            start_state="q0",
            accept_states=["q0"],
        )
        with pytest.raises(AlphabetMismatchError, match="Alphabets are not the same"):
            Automaton.test_equivalence(dfa1, dfa2)

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


# ---------------------------------------------------------------------------
# Helpers for NFA tests
# ---------------------------------------------------------------------------

def _make_nfa_ends_with_ab() -> NFA:
    """
    NFA over alphabet {a, b} that accepts exactly the strings ending with 'ab'.
    Language = [ab]*ab.

    States
    ------
    q0 : start, rejecting – general state
    q1 : intermediate     – last symbol was 'a', might be start of 'ab'
    q2 : accepting        – last two symbols were 'ab'

    Transitions (nondeterministic)
    ------------------------------
    q0 --a--> {q0, q1}   (stay in q0 OR guess 'a' starts the final 'ab')
    q0 --b--> {q0}
    q1 --b--> {q2}
    """
    return NFA(
        states=["q0", "q1", "q2"],
        alphabet="ab",
        transition_function={
            ("q0", "a"): {"q0", "q1"},
            ("q0", "b"): {"q0"},
            ("q1", "b"): {"q2"},
        },
        start_state="q0",
        accept_states=["q2"],
    )


def _make_nfa_epsilon() -> NFA:
    """
    NFA over alphabet {a, b} with epsilon transitions that accepts {a, ab}.

    States
    ------
    q0 : start
    q1 : reached after 'a' from q0
    q2 : accepting – epsilon-reachable from q1 (accepts 'a')
    q3 : accepting – reached after 'b' from q1 (accepts 'ab')

    Transitions
    -----------
    q0 --a--> {q1}
    q1 --ε--> {q2}
    q1 --b--> {q3}
    """
    return NFA(
        states=["q0", "q1", "q2", "q3"],
        alphabet="ab",
        transition_function={
            ("q0", "a"): {"q1"},
            ("q1", None): {"q2"},
            ("q1", "b"): {"q3"},
        },
        start_state="q0",
        accept_states=["q2", "q3"],
    )


# ---------------------------------------------------------------------------
# 5. NFA construction – validation tests
# ---------------------------------------------------------------------------

class TestNFAConstruction:
    def test_none_start_state_raises(self):
        with pytest.raises(InvalidStartStateError, match="Start state cannot be None"):
            NFA(
                states=["q0"],
                alphabet="a",
                transition_function={},
                start_state=None,
                accept_states=[],
            )

    def test_start_state_not_in_states_raises(self):
        with pytest.raises(InvalidStartStateError, match="Start state is not in the list of states"):
            NFA(
                states=["q0"],
                alphabet="a",
                transition_function={},
                start_state="q99",
                accept_states=[],
            )

    def test_accept_state_not_in_states_raises(self):
        with pytest.raises(InvalidAcceptStatesError, match="Accept states are not in the list of states"):
            NFA(
                states=["q0"],
                alphabet="a",
                transition_function={},
                start_state="q0",
                accept_states=["q99"],
            )

    def test_transition_from_unknown_state_raises(self):
        with pytest.raises(InvalidTransitionFunctionError, match="Transition function is not valid"):
            NFA(
                states=["q0"],
                alphabet="a",
                transition_function={("q99", "a"): {"q0"}},
                start_state="q0",
                accept_states=[],
            )

    def test_transition_with_unknown_symbol_raises(self):
        with pytest.raises(InvalidTransitionFunctionError, match="Transition function is not valid"):
            NFA(
                states=["q0"],
                alphabet="a",
                transition_function={("q0", "z"): {"q0"}},
                start_state="q0",
                accept_states=[],
            )

    def test_transition_to_unknown_state_raises(self):
        with pytest.raises(InvalidTransitionFunctionError, match="Transition function is not valid"):
            NFA(
                states=["q0"],
                alphabet="a",
                transition_function={("q0", "a"): {"q99"}},
                start_state="q0",
                accept_states=[],
            )

    def test_epsilon_transition_is_valid(self):
        """None as symbol key represents an epsilon transition and must be accepted."""
        nfa = NFA(
            states=["q0", "q1"],
            alphabet="a",
            transition_function={("q0", None): {"q1"}},
            start_state="q0",
            accept_states=["q1"],
        )
        assert nfa is not None

    def test_partial_transition_function_is_valid(self):
        """NFA allows a partial transition function (unlike DFA)."""
        nfa = NFA(
            states=["q0", "q1"],
            alphabet="ab",
            transition_function={("q0", "a"): {"q1"}},
            start_state="q0",
            accept_states=["q1"],
        )
        assert nfa is not None

    def test_valid_nfa_constructs_without_error(self):
        nfa = _make_nfa_ends_with_ab()
        assert nfa is not None


# ---------------------------------------------------------------------------
# 6. NFA.run() – deterministic unit tests
# ---------------------------------------------------------------------------

class TestNFARun:
    """
    NFA under test: _make_nfa_ends_with_ab()  (accepts [ab]*ab)

    Trace examples
    --------------
    ""    → {q0}  →  not accept  → False
    "a"   → {q0, q1}  →  not accept  → False
    "b"   → {q0}  →  not accept  → False
    "ab"  → {q0} → {q0, q1} → from q0: {q0}, from q1: {q2} = {q0, q2}  → True
    "ba"  → {q0} → {q0} → {q0, q1}  →  not accept  → False
    "aab" → {q0} → {q0,q1} → {q0,q1} → from q0:{q0}, from q1:{q2} = {q0,q2}  → True
    "abb" → {q0} → {q0,q1} → from q0:{q0}, from q1:{q2} = {q0,q2} → from q0:{q0}, q2:{} = {q0} → False
    """

    @pytest.fixture(autouse=True)
    def nfa(self):
        self.nfa = _make_nfa_ends_with_ab()

    def test_empty_string_rejected(self):
        assert self.nfa.run("") is False

    def test_single_a_rejected(self):
        assert self.nfa.run("a") is False

    def test_single_b_rejected(self):
        assert self.nfa.run("b") is False

    def test_ab_accepted(self):
        assert self.nfa.run("ab") is True

    def test_ba_rejected(self):
        assert self.nfa.run("ba") is False

    def test_aab_accepted(self):
        assert self.nfa.run("aab") is True

    def test_abb_rejected(self):
        assert self.nfa.run("abb") is False

    def test_bab_accepted(self):
        assert self.nfa.run("bab") is True

    def test_symbol_not_in_alphabet_raises(self):
        with pytest.raises(InvalidSymbolError, match="Symbol is not in the alphabet"):
            self.nfa.run("c")


class TestNFARunEpsilon:
    """
    NFA under test: _make_nfa_epsilon()  (accepts {a, ab})

    Trace examples
    --------------
    ""   → epsilon_closure({q0}) = {q0}  →  not accept  → False
    "a"  → from {q0} --a--> {q1}, epsilon_closure = {q1, q2}  → q2 is accept  → True
    "b"  → from {q0} --b--> {}, epsilon_closure = {}  →  not accept  → False
    "ab" → start {q0} --a--> {q1, q2} --b--> from q1:{q3}, from q2:{} = {q3},
           epsilon_closure({q3}) = {q3}  → q3 is accept  → True
    "aa" → start {q0} --a--> {q1,q2} --a--> from q1:{}, from q2:{} = {},
           epsilon_closure = {}  →  not accept  → False
    """

    @pytest.fixture(autouse=True)
    def nfa(self):
        self.nfa = _make_nfa_epsilon()

    def test_empty_string_rejected(self):
        assert self.nfa.run("") is False

    def test_single_a_accepted(self):
        assert self.nfa.run("a") is True

    def test_single_b_rejected(self):
        assert self.nfa.run("b") is False

    def test_ab_accepted(self):
        assert self.nfa.run("ab") is True

    def test_aa_rejected(self):
        assert self.nfa.run("aa") is False

    def test_ba_rejected(self):
        assert self.nfa.run("ba") is False


# ---------------------------------------------------------------------------
# 7. NFA.test() – property-based testing via Hypothesis
# ---------------------------------------------------------------------------

class TestNFATest:
    def test_correct_nfa_passes(self):
        """
        The 'ends with ab' NFA correctly implements [ab]*ab, so test() must
        return True.
        """
        nfa = _make_nfa_ends_with_ab()
        assert nfa.test("[ab]*ab") is True

    def test_incorrect_nfa_returns_counterexample(self):
        """
        This NFA has q0 as both start and accept state, so it incorrectly
        accepts the empty string and every string ending with 'b'. test()
        must return a counterexample.
        """
        buggy_nfa = NFA(
            states=["q0", "q1", "q2"],
            alphabet="ab",
            transition_function={
                ("q0", "a"): {"q0", "q1"},
                ("q0", "b"): {"q0"},
                ("q1", "b"): {"q2"},
            },
            start_state="q0",
            accept_states=["q0", "q2"],  # Bug: q0 should not be an accept state
        )
        result = buggy_nfa.test("[ab]*ab")

        assert result is not True
        assert isinstance(result, str)

        # The counterexample must actually witness the mismatch
        nfa_verdict = buggy_nfa.run(result)
        regex_verdict = bool(re.fullmatch("[ab]*ab", result))
        assert nfa_verdict != regex_verdict

    def test_correct_nfa_with_callable_passes(self):
        """NFA.test() also accepts a callable instead of a regex string."""
        nfa = _make_nfa_ends_with_ab()
        rule = lambda s: len(s) >= 2 and s[-2:] == "ab"
        assert nfa.test(rule) is True


# ---------------------------------------------------------------------------
# 8. NFA / DFA equivalence
# ---------------------------------------------------------------------------

class TestNFAEquivalence:
    def test_nfa_equivalent_to_dfa(self):
        """
        NFA for [ab]*ab must be equivalent to a DFA for the same language.
        """
        nfa = _make_nfa_ends_with_ab()
        dfa = DFA(
            states=["q0", "q1", "q2"],
            alphabet="ab",
            transition_function={
                ("q0", "a"): "q1",
                ("q0", "b"): "q0",
                ("q1", "a"): "q1",
                ("q1", "b"): "q2",
                ("q2", "a"): "q1",
                ("q2", "b"): "q0",
            },
            start_state="q0",
            accept_states=["q2"],
        )
        assert Automaton.test_equivalence(nfa, dfa) is True

    def test_non_equivalent_nfa_and_dfa_return_counterexample(self):
        """
        NFA for [ab]*ab vs DFA that accepts all strings — must return a
        counterexample (e.g. the empty string is accepted by DFA but not NFA).
        """
        nfa = _make_nfa_ends_with_ab()
        dfa_all = DFA(
            states=["q0"],
            alphabet="ab",
            transition_function={("q0", "a"): "q0", ("q0", "b"): "q0"},
            start_state="q0",
            accept_states=["q0"],
        )
        result = Automaton.test_equivalence(nfa, dfa_all)

        assert result is not True
        assert isinstance(result, str)
        assert nfa.run(result) != dfa_all.run(result)

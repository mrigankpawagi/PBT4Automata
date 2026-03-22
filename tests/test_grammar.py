"""Tests for grammar.py (CNF and CFG classes)."""

import pytest
from pbt4automata import (
    CNF,
    Grammar,
    InvalidGrammarSymbolError,
    InvalidNonterminalError,
    InvalidProductionError,
    InvalidStartSymbolError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_balanced_paren_cnf() -> CNF:
    """
    CNF for non-empty balanced-parentheses strings.  Productions:

        S → L X | S S      (balanced string)
        L → (              (open paren)
        R → )              (close paren)
        X → S R | )        (the "closing" part that pairs with an opening L)

    This grammar is taken directly from the README example.
    """
    return CNF(
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


def _check_balance(s: str) -> bool:
    """Reference implementation for balanced parentheses."""
    if s == "":
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


# ---------------------------------------------------------------------------
# 1. CNF construction – validation tests
# ---------------------------------------------------------------------------

class TestCNFConstruction:
    def test_none_start_symbol_raises(self):
        with pytest.raises(InvalidStartSymbolError, match="Start symbol cannot be None"):
            CNF(
                terminals="ab",
                nonterminals="S",
                productions={"S": ["a"]},
                start_symbol=None,
            )

    def test_start_symbol_not_in_nonterminals_raises(self):
        with pytest.raises(InvalidStartSymbolError, match="Start symbol is not in the list of nonterminals"):
            CNF(
                terminals="ab",
                nonterminals="S",
                productions={"S": ["a"]},
                start_symbol="X",
            )

    def test_unknown_nonterminal_in_productions_raises(self):
        with pytest.raises(InvalidNonterminalError, match="Nonterminal is not in the list of nonterminals"):
            CNF(
                terminals="a",
                nonterminals="S",
                productions={"Z": ["a"]},   # Z is not in nonterminals
                start_symbol="S",
            )

    def test_unknown_symbol_in_production_raises(self):
        with pytest.raises(InvalidGrammarSymbolError, match="Symbol is not in the list of terminals or nonterminals"):
            CNF(
                terminals="a",
                nonterminals="ST",
                productions={"S": ["TS"], "T": ["x"]},  # x not declared
                start_symbol="S",
            )

    def test_production_length_3_raises(self):
        # CNF does not allow productions of length > 2
        with pytest.raises(InvalidProductionError, match="Production is not in Chomsky normal form"):
            CNF(
                terminals="abc",
                nonterminals="SABC",
                productions={
                    "S": ["ABC"],   # length 3 – invalid
                    "A": ["a"],
                    "B": ["b"],
                    "C": ["c"],
                },
                start_symbol="S",
            )

    def test_length_1_production_with_nonterminal_raises(self):
        # A unit production A → B (where B is a nonterminal) violates CNF
        with pytest.raises(InvalidProductionError, match="Production is not in Chomsky normal form"):
            CNF(
                terminals="a",
                nonterminals="SAB",
                productions={
                    "S": ["AB"],
                    "A": ["B"],   # B is a nonterminal, not a terminal
                    "B": ["a"],
                },
                start_symbol="S",
            )

    def test_length_2_production_with_terminal_raises(self):
        # A → aB violates CNF (first symbol must be a nonterminal)
        with pytest.raises(InvalidProductionError, match="Production is not in Chomsky normal form"):
            CNF(
                terminals="a",
                nonterminals="SAB",
                productions={
                    "S": ["AB"],
                    "A": ["aB"],  # mixed terminal+nonterminal in length-2 rule
                    "B": ["a"],
                },
                start_symbol="S",
            )

    def test_valid_cnf_constructs_without_error(self):
        cnf = _make_balanced_paren_cnf()
        assert cnf is not None


# ---------------------------------------------------------------------------
# 2. CNF.parse() – deterministic CYK unit tests
#
#    The balanced-parentheses grammar is used.  Each expected value is derived
#    by tracing the CYK table; key traces are documented below.
#
#    "()"  trace
#    ----------
#    n=2, table[0][0]={L}, table[0][1]={R,X}
#    l=2,s=0,p=1: S→LX: L∈{L} and X∈{R,X} → table[1][0]={S}  → True ✓
#
#    "(())" trace (abbreviated)
#    ---------------------------
#    table[0]: {L}, {L}, {R,X}, {R,X}
#    After filling: S∈table[3][0] → True ✓
# ---------------------------------------------------------------------------

class TestCNFParse:
    @pytest.fixture(autouse=True)
    def cnf(self):
        self.cnf = _make_balanced_paren_cnf()

    # --- strings that should be accepted ---

    def test_parses_one_pair(self):
        assert self.cnf.parse("()") is True

    def test_parses_nested_pair(self):
        assert self.cnf.parse("(())") is True

    def test_parses_sequential_pairs(self):
        assert self.cnf.parse("()()") is True

    def test_parses_triple_nested(self):
        assert self.cnf.parse("((()))") is True

    def test_parses_mixed_nested_sequential(self):
        assert self.cnf.parse("(()(()))") is True

    # --- strings that should be rejected ---

    def test_rejects_single_open(self):
        assert self.cnf.parse("(") is False

    def test_rejects_single_close(self):
        assert self.cnf.parse(")") is False

    def test_rejects_reversed_pair(self):
        assert self.cnf.parse(")(") is False

    def test_rejects_unbalanced_extra_open(self):
        assert self.cnf.parse("(()") is False

    def test_rejects_unbalanced_extra_close(self):
        assert self.cnf.parse("())") is False


# ---------------------------------------------------------------------------
# 3. Simple CNF: S → a
#    Accepts exactly the single-character string "a".
# ---------------------------------------------------------------------------

class TestCNFSimpleSingleTerminal:
    @pytest.fixture(autouse=True)
    def cnf(self):
        self.cnf = CNF(
            terminals="ab",
            nonterminals="S",
            productions={"S": ["a"]},
            start_symbol="S",
        )

    def test_accepts_a(self):
        assert self.cnf.parse("a") is True

    def test_rejects_b(self):
        assert self.cnf.parse("b") is False

    def test_rejects_aa(self):
        assert self.cnf.parse("aa") is False


# ---------------------------------------------------------------------------
# 4. CNF.test() – property-based testing via Hypothesis
# ---------------------------------------------------------------------------

class TestCNFTest:
    def test_correct_grammar_passes(self):
        """
        The balanced-parentheses CNF correctly implements the language, so
        test() must return True (Hypothesis found no counterexample in 1000
        trials).
        """
        cnf = _make_balanced_paren_cnf()
        assert cnf.test(_check_balance) is True

    def test_incorrect_grammar_returns_counterexample(self):
        """
        This grammar is missing the S R alternative for X, so it cannot
        parse nested strings like "(())".  test() must return a counterexample.

        We validate the counterexample: the grammar and the reference
        implementation disagree on that exact string.
        """
        buggy_cnf = CNF(
            terminals="()",
            nonterminals="SLRX",
            productions={
                "S": ["LX", "SS"],
                "L": ["("],
                "R": [")"],
                "X": [")"],          # Bug: "SR" alternative removed
            },
            start_symbol="S",
        )
        result = buggy_cnf.test(_check_balance)

        assert result is not True
        assert isinstance(result, str)

        # The counterexample must actually witness the mismatch
        grammar_verdict = buggy_cnf.parse(result)
        reference_verdict = _check_balance(result)
        assert grammar_verdict != reference_verdict


# ---------------------------------------------------------------------------
# 5. Grammar.to_cnf() – conversion tests
# ---------------------------------------------------------------------------

def _make_simple_grammar() -> Grammar:
    """
    Simple grammar:  S → a | b
    Already trivially in CNF (single-terminal productions).
    """
    return Grammar(
        terminals="ab",
        nonterminals="S",
        productions={"S": ["a", "b"]},
        start_symbol="S",
    )


def _make_unit_production_grammar() -> Grammar:
    """
    Grammar with a unit production chain: S → A, A → a
    After CNF conversion the unit production S → A must be eliminated.
    """
    return Grammar(
        terminals="a",
        nonterminals="SA",
        productions={"S": ["A"], "A": ["a"]},
        start_symbol="S",
    )


def _make_long_production_grammar() -> Grammar:
    """
    Grammar with a length-3 production:  S → ABC, A → a, B → b, C → c
    to_cnf() must binarize S → ABC into two binary rules.
    """
    return Grammar(
        terminals="abc",
        nonterminals="SABC",
        productions={
            "S": ["ABC"],
            "A": ["a"],
            "B": ["b"],
            "C": ["c"],
        },
        start_symbol="S",
    )


def _make_epsilon_production_grammar() -> Grammar:
    """
    Grammar where A is nullable:
        S → AB, A → a | "", B → b
    The CNF must accept "ab" and "b" (when A derives ε), but not "a".
    """
    return Grammar(
        terminals="ab",
        nonterminals="SAB",
        productions={
            "S": ["AB"],
            "A": ["a", ""],
            "B": ["b"],
        },
        start_symbol="S",
    )


def _make_mixed_binary_grammar() -> Grammar:
    """
    Grammar with a mixed terminal/nonterminal binary production:
        S → aB, B → b
    The 'a' in 'aB' must be wrapped in a new nonterminal by to_cnf().
    """
    return Grammar(
        terminals="ab",
        nonterminals="SB",
        productions={
            "S": ["aB"],
            "B": ["b"],
        },
        start_symbol="S",
    )


class TestGrammarToCNF:
    def test_returns_cnf_instance(self):
        """to_cnf() must return a CNF object."""
        g = _make_simple_grammar()
        result = g.to_cnf()
        assert isinstance(result, CNF)

    def test_simple_grammar_preserves_language(self):
        """Grammar S → a | b accepts exactly 'a' and 'b'."""
        g = _make_simple_grammar()
        cnf = g.to_cnf()
        assert cnf.parse("a") is True
        assert cnf.parse("b") is True
        assert cnf.parse("ab") is False
        assert cnf.parse("c") is False

    def test_unit_production_elimination(self):
        """Grammar S → A, A → a: after CNF conversion S still accepts 'a'."""
        g = _make_unit_production_grammar()
        cnf = g.to_cnf()
        assert cnf.parse("a") is True
        assert cnf.parse("b") is False
        assert cnf.parse("aa") is False

    def test_long_production_binarization(self):
        """Grammar S → ABC must be binarized; CNF parses 'abc'."""
        g = _make_long_production_grammar()
        cnf = g.to_cnf()
        assert cnf.parse("abc") is True
        assert cnf.parse("ab") is False
        assert cnf.parse("abcd") is False
        assert cnf.parse("bca") is False

    def test_epsilon_production_elimination(self):
        """Grammar S → AB, A → a | ε, B → b: CNF accepts 'ab' and 'b'."""
        g = _make_epsilon_production_grammar()
        cnf = g.to_cnf()
        assert cnf.parse("ab") is True
        assert cnf.parse("b") is True
        assert cnf.parse("a") is False
        assert cnf.parse("") is False

    def test_mixed_binary_terminal_replacement(self):
        """Grammar S → aB, B → b: CNF must accept 'ab'."""
        g = _make_mixed_binary_grammar()
        cnf = g.to_cnf()
        assert cnf.parse("ab") is True
        assert cnf.parse("a") is False
        assert cnf.parse("b") is False
        assert cnf.parse("ba") is False

    def test_start_symbol_in_rhs(self):
        """
        When the start symbol appears on a RHS the conversion must introduce a
        new start symbol so the language is preserved.

        Grammar:  S → SS | a   (generates non-empty strings of 'a')
        """
        g = Grammar(
            terminals="a",
            nonterminals="S",
            productions={"S": ["SS", "a"]},
            start_symbol="S",
        )
        cnf = g.to_cnf()
        # S appears on the RHS of S → SS; a new start must have been introduced
        assert cnf.parse("a") is True
        assert cnf.parse("aa") is True
        assert cnf.parse("aaa") is True
        assert cnf.parse("b") is False

    def test_grammar_parse_delegates_to_cnf(self):
        """Grammar.parse() must match the CNF parse for several strings."""
        g = _make_long_production_grammar()
        cnf = g.to_cnf()
        for s in ["abc", "ab", "a", "b", "c", "abcd", ""]:
            assert g.parse(s) == cnf.parse(s)

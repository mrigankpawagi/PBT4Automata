"""Context-free grammar definitions and property-based testing utilities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence

from hypothesis import given, settings
from hypothesis import strategies as st

from pbt4automata.exceptions import (
    GrammarError,
    InvalidProductionError,
    InvalidStartSymbolError,
)

__all__ = ["CFG", "CNF", "Grammar"]


class CFG(ABC):
    """Abstract base class for context-free grammars."""

    #: Length of the longest string to test as a multiple of the number of
    #: productions.
    TEST_SCALE_FACTOR: int = 5

    @abstractmethod
    def parse(self, input_string: str) -> bool:
        """Return ``True`` if *input_string* is in the language of this grammar."""

    def test(self, rule: Callable[[str], bool]) -> bool | str:
        """Test the grammar against *rule* using property-based testing.

        Generates up to 1 000 non-empty strings from the terminal alphabet (up
        to length ``num_productions × TEST_SCALE_FACTOR``) and checks that the
        grammar agrees with *rule* on every one of them.

        Args:
            rule: A callable ``(str) -> bool`` that acts as the reference
                oracle.

        Returns:
            ``True`` if no counterexample was found, or the counterexample
            string (often the shortest one) if the grammar disagrees with
            *rule*.
        """
        alphabet = self.terminals
        num_productions = sum(len(p) for p in self.productions.values())

        @given(
            st.text(
                alphabet=alphabet,
                max_size=num_productions * CFG.TEST_SCALE_FACTOR,
                min_size=1,  # skip the empty string
            )
        )
        @settings(max_examples=1000)
        def _run(input_string: str) -> None:
            assert self.parse(input_string) == rule(input_string), input_string

        try:
            _run()
        except AssertionError as exc:
            return exc.args[0].split("\n")[0]

        return True


class CNF(CFG):
    """A context-free grammar in Chomsky Normal Form (CNF).

    Every production is either:

    * ``A → a``  — a single terminal symbol, or
    * ``A → B C`` — exactly two nonterminal symbols.

    The :meth:`parse` method uses the CYK (Cocke–Younger–Kasami) algorithm.

    Example:
        A CNF grammar for non-empty balanced-parentheses strings::

            cnf = CNF(
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
            cnf.parse("(())")  # returns True
    """

    def __init__(
        self,
        terminals: Sequence[str] | str,
        nonterminals: Sequence[str] | str,
        productions: dict[str, list[str]],
        start_symbol: str,
    ) -> None:
        """Initialise a CNF grammar.

        Args:
            terminals: Sequence of terminal symbols (single characters), or a
                string whose characters form the terminal alphabet.
            nonterminals: Sequence of nonterminal symbols (single characters),
                or a string whose characters form the nonterminal set.
            productions: Mapping ``{nonterminal: [rhs, ...]}``.  Each *rhs*
                must be either a one-character terminal or a two-character
                string of nonterminals.
            start_symbol: The start nonterminal.  Must be present in
                *nonterminals*.

        Raises:
            InvalidStartSymbolError: If *start_symbol* is ``None`` or not in
                *nonterminals*.
            GrammarError: If a production's left-hand side is not in
                *nonterminals*, or if a symbol on the right-hand side is
                neither a terminal nor a nonterminal.
            InvalidProductionError: If any production violates CNF
                constraints.
        """
        if start_symbol is None:
            raise InvalidStartSymbolError("Start symbol cannot be None")
        if start_symbol not in nonterminals:
            raise InvalidStartSymbolError("Start symbol is not in the list of nonterminals")

        for nonterminal, production in productions.items():
            if nonterminal not in nonterminals:
                raise GrammarError("Nonterminal is not in the list of nonterminals")
            for rhs in production:
                for symbol in rhs:
                    if symbol not in nonterminals and symbol not in terminals:
                        raise GrammarError(
                            "Symbol is not in the list of terminals or nonterminals: "
                            + symbol
                        )

        for nonterminal, production in productions.items():
            for rhs in production:
                if len(rhs) == 1:
                    if rhs[0] not in terminals:
                        raise InvalidProductionError(
                            f"Production is not in Chomsky normal form: {nonterminal} -> {rhs}"
                        )
                elif len(rhs) == 2:
                    if rhs[0] not in nonterminals or rhs[1] not in nonterminals:
                        raise InvalidProductionError(
                            f"Production is not in Chomsky normal form: {nonterminal} -> {rhs}"
                        )
                else:
                    raise InvalidProductionError(
                        f"Production is not in Chomsky normal form: {nonterminal} -> {rhs}"
                    )

        self.terminals: Sequence[str] | str = terminals
        self.nonterminals: Sequence[str] | str = nonterminals
        self.productions: dict[str, list[str]] = productions
        self.start_symbol: str = start_symbol

    def parse(self, input_string: str) -> bool:
        """Parse *input_string* using the CYK algorithm.

        Args:
            input_string: The string to parse.

        Returns:
            ``True`` if *input_string* is in the language, ``False`` otherwise.
        """
        n = len(input_string)
        table: list[list[set[str]]] = [[set() for _ in range(n)] for _ in range(n)]

        # Fill single-character cells.
        for i in range(n):
            for nonterminal, production in self.productions.items():
                for rhs in production:
                    if len(rhs) == 1 and rhs[0] == input_string[i]:
                        table[0][i].add(nonterminal)

        # Fill longer substrings by combining shorter ones.
        for length in range(2, n + 1):
            for start in range(n - length + 1):
                for split in range(1, length):
                    for nonterminal, production in self.productions.items():
                        for rhs in production:
                            if (
                                len(rhs) == 2
                                and rhs[0] in table[split - 1][start]
                                and rhs[1] in table[length - split - 1][start + split]
                            ):
                                table[length - 1][start].add(nonterminal)

        return self.start_symbol in table[n - 1][0]


class Grammar(CFG):
    """A general context-free grammar (not necessarily in CNF).

    .. note::
        :meth:`parse` requires conversion to CNF via :meth:`to_cnf`.
        Conversion is not yet implemented; calling :meth:`parse` will raise
        :exc:`NotImplementedError`.
    """

    def __init__(
        self,
        terminals: Sequence[str] | str,
        nonterminals: Sequence[str] | str,
        productions: dict[str, list[str]],
        start_symbol: str,
    ) -> None:
        """Initialise a general CFG.

        Args:
            terminals: Sequence of terminal symbols.
            nonterminals: Sequence of nonterminal symbols.
            productions: Mapping ``{nonterminal: [rhs, ...]}``.
            start_symbol: The start nonterminal.  Must be present in
                *nonterminals*.

        Raises:
            InvalidStartSymbolError: If *start_symbol* is ``None`` or not in
                *nonterminals*.
            GrammarError: If a production's left-hand side is not in
                *nonterminals*, or if a symbol on the right-hand side is
                neither a terminal nor a nonterminal.
        """
        if start_symbol is None:
            raise InvalidStartSymbolError("Start symbol cannot be None")
        if start_symbol not in nonterminals:
            raise InvalidStartSymbolError("Start symbol is not in the list of nonterminals")

        for nonterminal, production in productions.items():
            if nonterminal not in nonterminals:
                raise GrammarError("Nonterminal is not in the list of nonterminals")
            for rhs in production:
                for symbol in rhs:
                    if symbol not in nonterminals and symbol not in terminals:
                        raise GrammarError(
                            "Symbol is not in the list of terminals or nonterminals: "
                            + symbol
                        )

        self.terminals: Sequence[str] | str = terminals
        self.nonterminals: Sequence[str] | str = nonterminals
        self.productions: dict[str, list[str]] = productions
        self.start_symbol: str = start_symbol

    def to_cnf(self) -> CNF:
        """Convert this grammar to Chomsky Normal Form.

        Raises:
            NotImplementedError: This method is not yet implemented.
        """
        raise NotImplementedError("Conversion to CNF is not yet implemented.")

    def parse(self, input_string: str) -> bool:
        """Parse *input_string* by first converting to CNF, then applying CYK.

        Raises:
            NotImplementedError: Until :meth:`to_cnf` is implemented.
        """
        cnf = self.to_cnf()
        return cnf.parse(input_string)

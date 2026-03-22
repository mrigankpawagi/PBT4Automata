from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Sequence, TypeAlias

from hypothesis import given, settings, strategies as st

from .exceptions import (
    InvalidGrammarSymbolError,
    InvalidNonterminalError,
    InvalidProductionError,
    InvalidStartSymbolError,
)

Nonterminal: TypeAlias = str
Terminal: TypeAlias = str
Productions: TypeAlias = dict[Nonterminal, list[str]]
GrammarRule: TypeAlias = Callable[[str], bool]
TestResult: TypeAlias = bool | str


class CFG(ABC):
    TEST_SCALE_FACTOR = 5

    @property
    @abstractmethod
    def terminals(self) -> Sequence[Terminal]:
        """Terminal symbols supported by the grammar."""

    @property
    @abstractmethod
    def productions(self) -> Productions:
        """Grammar productions."""

    @abstractmethod
    def parse(self, input_string: str) -> bool:
        """Parse a string and decide membership in the language."""

    def test(self, rule: GrammarRule) -> TestResult:
        alphabet = self.terminals
        num_productions = sum(len(options) for options in self.productions.values())

        @given(
            st.text(
                alphabet=alphabet,
                max_size=num_productions * CFG.TEST_SCALE_FACTOR,
                min_size=1,
            )
        )
        @settings(max_examples=1000)
        def run_case(input_string: str) -> None:
            assert self.parse(input_string) == rule(input_string), input_string

        try:
            run_case()
        except AssertionError as err:
            return str(err.args[0]).split("\n")[0]
        return True


class CNF(CFG):
    def __init__(
        self,
        terminals: Sequence[Terminal] | str,
        nonterminals: Sequence[Nonterminal] | str,
        productions: Productions,
        start_symbol: Nonterminal | None,
    ) -> None:
        normalized_terminals = tuple(terminals)
        normalized_nonterminals = tuple(nonterminals)

        if start_symbol is None:
            raise InvalidStartSymbolError("Start symbol cannot be None")
        if start_symbol not in normalized_nonterminals:
            raise InvalidStartSymbolError("Start symbol is not in the list of nonterminals")

        for nonterminal, alternatives in productions.items():
            if nonterminal not in normalized_nonterminals:
                raise InvalidNonterminalError("Nonterminal is not in the list of nonterminals")
            for production in alternatives:
                for symbol in production:
                    if symbol not in normalized_nonterminals and symbol not in normalized_terminals:
                        raise InvalidGrammarSymbolError(
                            "Symbol is not in the list of terminals or nonterminals: " + symbol
                        )

        for nonterminal, alternatives in productions.items():
            for production in alternatives:
                if len(production) == 1:
                    if production[0] not in normalized_terminals:
                        raise InvalidProductionError(
                            f"Production is not in Chomsky normal form: {nonterminal} -> {production}"
                        )
                elif len(production) == 2:
                    if (
                        production[0] not in normalized_nonterminals
                        or production[1] not in normalized_nonterminals
                    ):
                        raise InvalidProductionError(
                            f"Production is not in Chomsky normal form: {nonterminal} -> {production}"
                        )
                else:
                    raise InvalidProductionError(
                        f"Production is not in Chomsky normal form: {nonterminal} -> {production}"
                    )

        self._terminals = normalized_terminals
        self.nonterminals = normalized_nonterminals
        self._productions = productions
        self.start_symbol = start_symbol

    @property
    def terminals(self) -> Sequence[Terminal]:
        return self._terminals

    @property
    def productions(self) -> Productions:
        return self._productions

    def parse(self, input_string: str) -> bool:
        n = len(input_string)
        if n == 0:
            return False

        table = [[set() for _ in range(n)] for _ in range(n)]

        for i in range(n):
            for nonterminal, alternatives in self.productions.items():
                for production in alternatives:
                    if len(production) == 1 and production[0] == input_string[i]:
                        table[0][i].add(nonterminal)

        for length in range(2, n + 1):
            for start in range(n - length + 1):
                for split in range(1, length):
                    for nonterminal, alternatives in self.productions.items():
                        for production in alternatives:
                            if (
                                len(production) == 2
                                and production[0] in table[split - 1][start]
                                and production[1] in table[length - split - 1][start + split]
                            ):
                                table[length - 1][start].add(nonterminal)

        return self.start_symbol in table[n - 1][0]


class Grammar(CFG):
    def __init__(
        self,
        terminals: Sequence[Terminal] | str,
        nonterminals: Sequence[Nonterminal] | str,
        productions: Productions,
        start_symbol: Nonterminal | None,
    ) -> None:
        normalized_terminals = tuple(terminals)
        normalized_nonterminals = tuple(nonterminals)

        if start_symbol is None:
            raise InvalidStartSymbolError("Start symbol cannot be None")
        if start_symbol not in normalized_nonterminals:
            raise InvalidStartSymbolError("Start symbol is not in the list of nonterminals")

        for nonterminal, alternatives in productions.items():
            if nonterminal not in normalized_nonterminals:
                raise InvalidNonterminalError("Nonterminal is not in the list of nonterminals")
            for production in alternatives:
                for symbol in production:
                    if symbol not in normalized_nonterminals and symbol not in normalized_terminals:
                        raise InvalidGrammarSymbolError(
                            "Symbol is not in the list of terminals or nonterminals: " + symbol
                        )

        self._terminals = normalized_terminals
        self.nonterminals = normalized_nonterminals
        self._productions = productions
        self.start_symbol = start_symbol

    @property
    def terminals(self) -> Sequence[Terminal]:
        return self._terminals

    @property
    def productions(self) -> Productions:
        return self._productions

    def to_cnf(self) -> CNF:
        raise NotImplementedError("Conversion to CNF is not implemented yet.")

    def parse(self, input_string: str) -> bool:
        cnf = self.to_cnf()
        return cnf.parse(input_string)

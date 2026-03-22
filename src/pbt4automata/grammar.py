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
        terminals: set[str] = set(self._terminals)
        nonterminals: set[str] = set(self.nonterminals)

        # Internal representation: dict[str, set[tuple[str, ...]]]
        # Each production is a tuple of single-character symbols.
        prods: dict[str, set[tuple[str, ...]]] = {
            nt: {tuple(alt) for alt in alts}
            for nt, alts in self._productions.items()
        }
        # Ensure every declared nonterminal has an entry (even if no productions).
        for nt in nonterminals:
            prods.setdefault(nt, set())

        start = self.start_symbol

        # Helper: allocate a fresh single-character nonterminal symbol.
        # Using an iterator keeps the total allocation cost O(|alphabet|)
        # rather than O(n²) when many new symbols are needed.
        _used: set[str] = terminals | nonterminals
        _nt_candidates = iter(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz"
            "0123456789"
        )

        def new_nt() -> str:
            for c in _nt_candidates:
                if c not in _used:
                    _used.add(c)
                    nonterminals.add(c)
                    prods[c] = set()
                    return c
            raise ValueError("No available single-character nonterminal symbols remain")

        # ── Step 1: New start symbol ──────────────────────────────────────────
        # Ensure the current start symbol does not appear on any right-hand side.
        start_in_rhs = any(
            start in sym
            for alts in prods.values()
            for prod in alts
            for sym in prod
        )
        if start_in_rhs:
            new_start = new_nt()
            prods[new_start] = {(start,)}
            start = new_start

        # ── Step 2: Eliminate ε-productions ──────────────────────────────────
        # Compute the set of nullable nonterminals (those that can derive ε).
        nullable: set[str] = set()
        for nt, alts in prods.items():
            for prod in alts:
                if not prod:
                    nullable.add(nt)

        changed = True
        while changed:
            changed = False
            for nt, alts in prods.items():
                if nt not in nullable:
                    for prod in alts:
                        if prod and all(sym in nullable for sym in prod):
                            nullable.add(nt)
                            changed = True

        # Rebuild productions: drop ε-rules and add nullable-omission variants.
        new_prods: dict[str, set[tuple[str, ...]]] = {nt: set() for nt in prods}
        for nt, alts in prods.items():
            for prod in alts:
                if not prod:
                    continue  # drop ε-production
                nullable_positions = [i for i, sym in enumerate(prod) if sym in nullable]
                num_nullable = len(nullable_positions)
                for mask in range(1 << num_nullable):
                    omit = {
                        nullable_positions[j]
                        for j in range(num_nullable)
                        if mask & (1 << j)
                    }
                    new_prod = tuple(sym for i, sym in enumerate(prod) if i not in omit)
                    if new_prod:  # never re-introduce ε
                        new_prods[nt].add(new_prod)
        prods = new_prods

        # ── Step 3: Eliminate unit productions ───────────────────────────────
        def unit_closure(root: str) -> set[str]:
            visited: set[str] = {root}
            queue: list[str] = [root]
            while queue:
                current = queue.pop()
                for prod in prods.get(current, set()):
                    if (
                        len(prod) == 1
                        and prod[0] in nonterminals
                        and prod[0] not in visited
                    ):
                        visited.add(prod[0])
                        queue.append(prod[0])
            return visited

        for nt in list(prods.keys()):
            closure = unit_closure(nt)
            combined: set[tuple[str, ...]] = set()
            for b in closure:
                for prod in prods.get(b, set()):
                    if not (len(prod) == 1 and prod[0] in nonterminals):
                        combined.add(prod)
            prods[nt] = combined

        # ── Step 4: Binarize long productions (length ≥ 3) ───────────────────
        for nt in list(prods.keys()):
            long_prods = {prod for prod in prods[nt] if len(prod) > 2}
            for prod in long_prods:
                prods[nt].discard(prod)
                remaining = list(prod)
                current_nt = nt
                while len(remaining) > 2:
                    first = remaining[0]
                    remaining = remaining[1:]
                    next_nt = new_nt()
                    prods[current_nt].add((first, next_nt))
                    current_nt = next_nt
                prods[current_nt].add(tuple(remaining))

        # ── Step 5: Replace terminals in binary productions ───────────────────
        # For A → BC where B or C is a terminal, introduce Tₐ → a.
        terminal_nt: dict[str, str] = {}
        for nt in list(prods.keys()):
            new_alts: set[tuple[str, ...]] = set()
            for prod in prods[nt]:
                if len(prod) == 2:
                    new_prod = list(prod)
                    for i in range(2):
                        if new_prod[i] in terminals:
                            a = new_prod[i]
                            if a not in terminal_nt:
                                terminal_nt[a] = new_nt()
                            new_prod[i] = terminal_nt[a]
                    new_alts.add(tuple(new_prod))
                else:
                    new_alts.add(prod)
            prods[nt] = new_alts

        for terminal, wrapper_nt in terminal_nt.items():
            prods[wrapper_nt] = {(terminal,)}

        # ── Assemble the CNF object ───────────────────────────────────────────
        active_nts = {nt for nt, alts in prods.items() if alts}
        active_nts.add(start)

        final_prods: Productions = {
            nt: ["".join(prod) for prod in prods[nt]]
            for nt in active_nts
            if prods.get(nt)
        }

        return CNF(
            terminals=list(terminals),
            nonterminals=list(active_nts),
            productions=final_prods,
            start_symbol=start,
        )

    def parse(self, input_string: str) -> bool:
        cnf = self.to_cnf()
        return cnf.parse(input_string)

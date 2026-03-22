"""Custom exception hierarchy for pbt4automata."""


class PBT4AutomataError(Exception):
    """Base exception for all library errors."""


class AutomatonError(PBT4AutomataError):
    """Base exception for automaton-related errors."""


class InvalidStartStateError(AutomatonError):
    """Raised when a DFA start state is missing or invalid."""


class InvalidAcceptStatesError(AutomatonError):
    """Raised when one or more DFA accept states are invalid."""


class InvalidTransitionFunctionError(AutomatonError):
    """Raised when a DFA transition function is incomplete or invalid."""


class InvalidSymbolError(AutomatonError):
    """Raised when an input symbol is not in the alphabet."""


class AlphabetMismatchError(AutomatonError):
    """Raised when equivalence testing is requested for different alphabets."""


class GrammarError(PBT4AutomataError):
    """Base exception for grammar-related errors."""


class InvalidStartSymbolError(GrammarError):
    """Raised when a grammar start symbol is missing or invalid."""


class InvalidNonterminalError(GrammarError):
    """Raised when productions reference undeclared nonterminals."""


class InvalidGrammarSymbolError(GrammarError):
    """Raised when productions reference undeclared terminals/nonterminals."""


class InvalidProductionError(GrammarError):
    """Raised when grammar productions violate expected constraints."""

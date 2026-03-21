"""Custom exceptions for pbt4automata."""

from __future__ import annotations

__all__ = [
    "PBT4AutomataError",
    "AutomatonError",
    "InvalidStartStateError",
    "InvalidAcceptStatesError",
    "InvalidTransitionFunctionError",
    "InvalidSymbolError",
    "GrammarError",
    "InvalidStartSymbolError",
    "InvalidProductionError",
]


class PBT4AutomataError(Exception):
    """Base exception for all pbt4automata errors."""


# ---------------------------------------------------------------------------
# Automaton exceptions
# ---------------------------------------------------------------------------


class AutomatonError(PBT4AutomataError):
    """Base exception for automaton-related errors."""


class InvalidStartStateError(AutomatonError):
    """Raised when the start state is ``None`` or not present in the state set."""


class InvalidAcceptStatesError(AutomatonError):
    """Raised when one or more accept states are not present in the state set."""


class InvalidTransitionFunctionError(AutomatonError):
    """Raised when the transition function is incomplete or references unknown states."""


class InvalidSymbolError(AutomatonError):
    """Raised when a symbol outside the alphabet is encountered during execution."""


# ---------------------------------------------------------------------------
# Grammar exceptions
# ---------------------------------------------------------------------------


class GrammarError(PBT4AutomataError):
    """Base exception for grammar-related errors."""


class InvalidStartSymbolError(GrammarError):
    """Raised when the start symbol is ``None`` or not present in the nonterminal set."""


class InvalidProductionError(GrammarError):
    """Raised when a production rule violates the grammar's normal-form constraints."""

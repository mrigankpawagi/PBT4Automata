from __future__ import annotations
from abc import ABC
from hypothesis import given, strategies as st, settings
from typing import Callable


class CFG(ABC):
    TEST_SCALE_FACTOR = 5 # length of the longest string to test as a multiple of the number of productions
    
    def test(self, rule: Callable[[str], bool]):
        """
        Uses hypothesis to test the automaton against the 
        given rule (function)
        
        The function must be be of type Callable[[str], bool]
        """
        alphabet = self.terminals
        num_productions = sum(len(p) for p in self.productions.values())
        
        counter_example = None
        
        @given(st.text(alphabet=alphabet, max_size=num_productions * CFG.TEST_SCALE_FACTOR, min_size=1)) # skip empty strings
        @settings(max_examples=1000)
        def run(input_string):       
            # Parse the input string with the CFG
            result = self.parse(input_string)
            
            # Check if the result matches the result from the rule
            assert result == rule(input_string), input_string

        try:
            run()
        except AssertionError as e:
            # If the assertion fails, we return a counter example
            counter_example = e.args[0].split("\n")[0]
            return counter_example
            
        return True


class CNF(CFG):
    """
    A context-free grammar in Chomsky normal form. 
    """
    
    def __init__(self, terminals: list[str] | str, nonterminals: list[str] | str, productions: dict[str, list[str]], start_symbol: str):
        """
        Initialize the CNF with the given parameters.
        
        terminals: sequence of terminal symbols
        nonterminals: sequence of nonterminal symbols
        productions: dictionary of productions of the form {nonterminal: [productions...]}
        start_symbol: the starting nonterminal symbol
        """
        # Start symbol must not be None
        if start_symbol is None:
            raise Exception("Start symbol cannot be None")
        
        # Check if start symbol is in the list of nonterminals
        if start_symbol not in nonterminals:
            raise Exception("Start symbol is not in the list of nonterminals")
        
        # Check if all nonterminals in the productions are in the list of nonterminals
        # and all terminals in the productions are in the list of terminals
        for nonterminal, production in productions.items():
            if nonterminal not in nonterminals:
                raise Exception("Nonterminal is not in the list of nonterminals")
            for p in production:
                for symbol in p:
                    if symbol not in nonterminals and symbol not in terminals:
                        raise Exception("Symbol is not in the list of terminals or nonterminals: " + symbol)
        
        # Check that all productions are in Chomsky normal form
        for nonterminal, production in productions.items():
            for p in production:
                if len(p) == 1:
                    if p[0] not in terminals:
                        raise Exception(f"Production is not in Chomsky normal form: {nonterminal} -> {p}")
                elif len(p) == 2:
                    if p[0] not in nonterminals or p[1] not in nonterminals:
                        raise Exception(f"Production is not in Chomsky normal form: {nonterminal} -> {p}")
                else:
                    raise Exception(f"Production is not in Chomsky normal form: {nonterminal} -> {p}")

        self.terminals = terminals
        self.nonterminals = nonterminals
        self.productions = productions
        self.start_symbol = start_symbol
        
    def parse(self, input_string: str) -> bool:
        """
        Parse the input string using the CYK algorithm.
        
        input_string: string to parse
        """
        # Create a table to store the parse results
        n = len(input_string)
        table = [[set() for _ in range(n)] for i in range(n)]

        # Fill in the table
        for i in range(n):
            for nonterminal, production in self.productions.items():
                for p in production:
                    if len(p) == 1 and p[0] == input_string[i]:
                        table[0][i].add(nonterminal)
                        
        for l in range(2, n + 1):
            for s in range(n - l + 1):
                for p in range(1, l):
                    for nonterminal, production in self.productions.items():
                        for pr in production:
                            if len(pr) == 2 and pr[0] in table[p - 1][s] and pr[1] in table[l - p - 1][s + p]:
                                table[l - 1][s].add(nonterminal)
                                
        # Check if the start symbol is in the table
        return self.start_symbol in table[n - 1][0]
    

class Grammar(CFG):
    """
    A context-free grammar.
    """
    
    def __init__(self, terminals: list[str] | str, nonterminals: list[str] | str, productions: dict[str, list[str]], start_symbol: str):
        """
        Initialize the grammar with the given parameters.
        
        terminals: sequence of terminal symbols
        nonterminals: sequence of nonterminal symbols
        productions: dictionary of productions of the form {nonterminal: [productions...]}
        start_symbol: the starting nonterminal symbol
        """
        # Start symbol must not be None
        if start_symbol is None:
            raise Exception("Start symbol cannot be None")
        
        # Check if start symbol is in the list of nonterminals
        if start_symbol not in nonterminals:
            raise Exception("Start symbol is not in the list of nonterminals")
        
        # Check if all nonterminals in the productions are in the list of nonterminals
        # and all terminals in the productions are in the list of terminals
        for nonterminal, production in productions.items():
            if nonterminal not in nonterminals:
                raise Exception("Nonterminal is not in the list of nonterminals")
            for p in production:
                for symbol in p:
                    if symbol not in nonterminals and symbol not in terminals:
                        raise Exception("Symbol is not in the list of terminals or nonterminals: " + symbol)
        
        self.terminals = terminals
        self.nonterminals = nonterminals
        self.productions = productions
        self.start_symbol = start_symbol
        
    def to_cnf(self) -> CNF:
        """
        Convert the grammar to Chomsky normal form.
        """
        pass                    
        
    def parse(self, input_string: str) -> bool:
        """
        Parse the input string using the CYK algorithm, by first
        converting the grammar to Chomsky normal form.
        """
        cnf = self.to_cnf()
        return cnf.parse(input_string)

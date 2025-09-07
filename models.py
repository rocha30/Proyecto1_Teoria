"""
Modelos de datos para autómatas finitos.
Contiene las definiciones de NFAState, NFA, DFAState y DFA.
"""

class NFAState:
    """Estado de un Autómata Finito No Determinista"""
    def __init__(self, state_id, is_final=False):
        self.id = state_id
        self.is_final = is_final
        self.transitions = {}  # {symbol: [list_of_states]}
        self.epsilon_transitions = []  # Lista de estados alcanzables con ε
    
    def add_transition(self, symbol, target_state):
        """Agregar transición con símbolo"""
        if symbol not in self.transitions:
            self.transitions[symbol] = []
        self.transitions[symbol].append(target_state)
    
    def add_epsilon_transition(self, target_state):
        """Agregar transición epsilon"""
        self.epsilon_transitions.append(target_state)
    
    def __repr__(self):
        return f"State({self.id}{'*' if self.is_final else ''})"


class NFA:
    """Autómata Finito No Determinista"""
    def __init__(self, start_state, final_states):
        self.start_state = start_state
        self.final_states = final_states if isinstance(final_states, list) else [final_states]
        self.states = set()
        self.alphabet = set()
        self._collect_states_and_alphabet()
    
    def _collect_states_and_alphabet(self):
        """Recolectar todos los estados y símbolos del alfabeto"""
        visited = set()
        stack = [self.start_state] + self.final_states
        
        while stack:
            state = stack.pop()
            if state in visited:
                continue
            visited.add(state)
            self.states.add(state)
            
            # Agregar transiciones normales
            for symbol, target_states in state.transitions.items():
                self.alphabet.add(symbol)
                for target in target_states:
                    if target not in visited:
                        stack.append(target)
            
            # Agregar transiciones epsilon
            for target in state.epsilon_transitions:
                if target not in visited:
                    stack.append(target)
    
    def get_epsilon_closure(self, states):
        """Obtener clausura epsilon de un conjunto de estados"""
        closure = set(states)
        stack = list(states)
        
        while stack:
            state = stack.pop()
            for epsilon_target in state.epsilon_transitions:
                if epsilon_target not in closure:
                    closure.add(epsilon_target)
                    stack.append(epsilon_target)
        
        return closure
    
    def simulate(self, input_string):
        """Simular el AFN con una cadena de entrada"""
        current_states = self.get_epsilon_closure([self.start_state])
        
        for symbol in input_string:
            next_states = set()
            for state in current_states:
                if symbol in state.transitions:
                    next_states.update(state.transitions[symbol])
            
            if not next_states:
                return False
            
            current_states = self.get_epsilon_closure(next_states)
        
        # Verificar si algún estado actual es final
        return any(state.is_final for state in current_states)


class DFAState:
    """Estado de un Autómata Finito Determinista"""
    def __init__(self, state_id, nfa_states=None, is_final=False):
        self.id = state_id
        self.nfa_states = nfa_states if nfa_states else set()  # Estados del AFN que representa
        self.is_final = is_final
        self.transitions = {}  # {symbol: target_state}
    
    def add_transition(self, symbol, target_state):
        """Agregar transición determinista"""
        self.transitions[symbol] = target_state
    
    def __repr__(self):
        return f"DFAState({self.id}{'*' if self.is_final else ''})"
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return isinstance(other, DFAState) and self.id == other.id


class DFA:
    """Autómata Finito Determinista"""
    def __init__(self, start_state, final_states, alphabet):
        self.start_state = start_state
        self.final_states = final_states if isinstance(final_states, set) else set(final_states)
        self.alphabet = alphabet
        self.states = set()
        self._collect_states()
    
    def _collect_states(self):
        """Recolectar todos los estados del AFD"""
        visited = set()
        stack = [self.start_state] + list(self.final_states)
        
        while stack:
            state = stack.pop()
            if state in visited:
                continue
            visited.add(state)
            self.states.add(state)
            
            # Agregar estados alcanzables
            for target_state in state.transitions.values():
                if target_state not in visited:
                    stack.append(target_state)
    
    def simulate(self, input_string):
        """Simular el AFD con una cadena de entrada"""
        current_state = self.start_state
        
        for symbol in input_string:
            if symbol not in current_state.transitions:
                return False
            current_state = current_state.transitions[symbol]
        
        return current_state in self.final_states
    
    def get_states_count(self):
        """Obtener número de estados"""
        return len(self.states)
    
    def get_transitions_count(self):
        """Obtener número de transiciones"""
        return sum(len(state.transitions) for state in self.states)

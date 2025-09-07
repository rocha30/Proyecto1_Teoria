"""
Constructores de autómatas: Thompson, Construcción por Subconjuntos y Minimización.
Implementa los algoritmos para convertir AST → AFN → AFD → AFD Minimizado.
"""

try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

from models import NFAState, NFA, DFAState, DFA


class ThompsonNFAConstructor:
    """Constructor de AFN usando el Algoritmo de Thompson"""
    
    def __init__(self):
        self.state_counter = 0
    
    def new_state(self, is_final=False):
        """Crear un nuevo estado con ID único"""
        state = NFAState(self.state_counter, is_final)
        self.state_counter += 1
        return state
    
    def construct_nfa(self, ast_root):
        """Construir AFN desde AST usando Thompson"""
        if ast_root is None:
            return None
        
        self.state_counter = 0
        return self._build_nfa_recursive(ast_root)
    
    def _build_nfa_recursive(self, node):
        """Construir AFN recursivamente desde un nodo AST"""
        if node.is_leaf():
            # Caso base: símbolo terminal
            return self._construct_basic(node.value)
        
        # Casos recursivos según el operador
        if node.value == '.':  # Concatenación
            left_nfa = self._build_nfa_recursive(node.left)
            right_nfa = self._build_nfa_recursive(node.right)
            return self._construct_concatenation(left_nfa, right_nfa)
        
        elif node.value == '|':  # Unión
            left_nfa = self._build_nfa_recursive(node.left)
            right_nfa = self._build_nfa_recursive(node.right)
            return self._construct_union(left_nfa, right_nfa)
        
        elif node.value == '*':  # Estrella de Kleene
            child_nfa = self._build_nfa_recursive(node.left)
            return self._construct_kleene_star(child_nfa)
        
        else:
            raise ValueError(f"Operador no soportado: {node.value}")
    
    def _construct_basic(self, symbol):
        """Construcción Thompson para símbolo básico"""
        start = self.new_state()
        final = self.new_state(is_final=True)
        
        # Manejar símbolos especiales
        if symbol == 'ε':
            start.add_epsilon_transition(final)
        elif symbol.startswith('L'):
            # Literal escapado - usar el carácter sin el prefijo L
            actual_symbol = symbol[1:] if len(symbol) > 1 else symbol
            start.add_transition(actual_symbol, final)
        else:
            start.add_transition(symbol, final)
        
        return NFA(start, final)
    
    def _construct_concatenation(self, nfa1, nfa2):
        """Construcción Thompson para concatenación"""
        # Conectar estados finales de nfa1 con estado inicial de nfa2
        for final_state in nfa1.final_states:
            final_state.is_final = False
            final_state.add_epsilon_transition(nfa2.start_state)
        
        return NFA(nfa1.start_state, nfa2.final_states)
    
    def _construct_union(self, nfa1, nfa2):
        """Construcción Thompson para unión (|)"""
        new_start = self.new_state()
        new_final = self.new_state(is_final=True)
        
        # Conectar nuevo inicio con inicios de ambos AFNs
        new_start.add_epsilon_transition(nfa1.start_state)
        new_start.add_epsilon_transition(nfa2.start_state)
        
        # Conectar finales de ambos AFNs con nuevo final
        for final_state in nfa1.final_states + nfa2.final_states:
            final_state.is_final = False
            final_state.add_epsilon_transition(new_final)
        
        return NFA(new_start, new_final)
    
    def _construct_kleene_star(self, nfa):
        """Construcción Thompson para estrella de Kleene (*)"""
        new_start = self.new_state()
        new_final = self.new_state(is_final=True)
        
        # Epsilon desde nuevo inicio a nuevo final (cero repeticiones)
        new_start.add_epsilon_transition(new_final)
        
        # Epsilon desde nuevo inicio al inicio del AFN original
        new_start.add_epsilon_transition(nfa.start_state)
        
        # Epsilon desde finales del AFN original al nuevo final
        for final_state in nfa.final_states:
            final_state.is_final = False
            final_state.add_epsilon_transition(new_final)
            # Epsilon de vuelta al inicio para repeticiones
            final_state.add_epsilon_transition(nfa.start_state)
        
        return NFA(new_start, new_final)
    
    def visualize_nfa(self, nfa, filename="thompson_nfa", format="png"):
        """Visualizar AFN usando Graphviz"""
        if not GRAPHVIZ_AVAILABLE:
            print(" No se puede visualizar: Graphviz no está disponible")
            return None
        
        dot = graphviz.Digraph(comment='Thompson NFA')
        dot.attr(rankdir='LR')  # Left to Right
        dot.attr('node', shape='circle')
        
        # Agregar nodos
        for state in nfa.states:
            if state.is_final:
                dot.node(str(state.id), str(state.id), shape='doublecircle', style='filled', fillcolor='lightgreen')
            elif state == nfa.start_state:
                dot.node(str(state.id), str(state.id), style='filled', fillcolor='lightblue')
            else:
                dot.node(str(state.id), str(state.id))
        
        # Agregar estado invisible para flecha de inicio
        dot.node('start', '', shape='point')
        dot.edge('start', str(nfa.start_state.id), label='start')
        
        # Agregar transiciones
        for state in nfa.states:
            # Transiciones con símbolos
            for symbol, target_states in state.transitions.items():
                for target in target_states:
                    dot.edge(str(state.id), str(target.id), label=symbol)
            
            # Transiciones epsilon
            for target in state.epsilon_transitions:
                dot.edge(str(state.id), str(target.id), label='ε', style='dashed')
        
        try:
            dot.render(filename, format=format, cleanup=True)
            print(f"    AFN visualizado en: {filename}.{format}")
            return dot
        except Exception as e:
            print(f"    Error al generar visualización del AFN: {e}")
            return None


class SubsetConstructor:
    """Constructor de AFD usando el algoritmo de construcción por subconjuntos"""
    
    def __init__(self):
        self.state_counter = 0
        self.subset_to_dfa_state = {}  # Mapeo de conjuntos de estados AFN a estados AFD
    
    def construct_dfa(self, nfa):
        """Construir AFD desde AFN usando construcción por subconjuntos"""
        print(f"    🔄 Iniciando construcción por subconjuntos...")
        
        # Reiniciar contadores
        self.state_counter = 0
        self.subset_to_dfa_state = {}
        
        # Estado inicial del AFD: clausura epsilon del estado inicial del AFN
        initial_subset = nfa.get_epsilon_closure([nfa.start_state])
        initial_dfa_state = self._get_or_create_dfa_state(initial_subset, nfa.final_states)
        
        # Cola de subconjuntos por procesar
        worklist = [initial_subset]
        processed = set()
        dfa_states = {initial_dfa_state}
        final_dfa_states = set()
        
        if initial_dfa_state.is_final:
            final_dfa_states.add(initial_dfa_state)
        
        print(f"      Estado inicial AFD: {initial_dfa_state.id} = {{{', '.join(str(s.id) for s in initial_subset)}}}")
        
        while worklist:
            current_subset = worklist.pop(0)
            current_subset_key = self._subset_to_key(current_subset)
            
            if current_subset_key in processed:
                continue
            processed.add(current_subset_key)
            
            current_dfa_state = self.subset_to_dfa_state[current_subset_key]
            
            # Para cada símbolo del alfabeto
            for symbol in sorted(nfa.alphabet):
                # Calcular el conjunto de estados alcanzables con este símbolo
                next_subset = set()
                for nfa_state in current_subset:
                    if symbol in nfa_state.transitions:
                        next_subset.update(nfa_state.transitions[symbol])
                
                if next_subset:
                    # Aplicar clausura epsilon
                    next_subset = nfa.get_epsilon_closure(next_subset)
                    next_dfa_state = self._get_or_create_dfa_state(next_subset, nfa.final_states)
                    
                    # Agregar transición al AFD
                    current_dfa_state.add_transition(symbol, next_dfa_state)
                    
                    # Agregar a conjuntos correspondientes
                    dfa_states.add(next_dfa_state)
                    if next_dfa_state.is_final:
                        final_dfa_states.add(next_dfa_state)
                    
                    # Agregar a cola si no ha sido procesado
                    next_subset_key = self._subset_to_key(next_subset)
                    if next_subset_key not in processed:
                        worklist.append(next_subset)
                    
                    print(f"      δ({current_dfa_state.id}, {symbol}) = {next_dfa_state.id}")
        
        # Crear AFD final
        dfa = DFA(initial_dfa_state, final_dfa_states, nfa.alphabet)
        
        print(f"    ✅ AFD construido:")
        print(f"      - Estados: {len(dfa.states)}")
        print(f"      - Estados finales: {len(final_dfa_states)}")
        print(f"      - Transiciones: {dfa.get_transitions_count()}")
        
        return dfa
    
    def _get_or_create_dfa_state(self, nfa_subset, nfa_final_states):
        """Obtener o crear estado AFD para un subconjunto de estados AFN"""
        subset_key = self._subset_to_key(nfa_subset)
        
        if subset_key in self.subset_to_dfa_state:
            return self.subset_to_dfa_state[subset_key]
        
        # Determinar si es estado final
        is_final = any(nfa_state in nfa_final_states for nfa_state in nfa_subset)
        
        # Crear nuevo estado AFD
        dfa_state = DFAState(self.state_counter, nfa_subset, is_final)
        self.state_counter += 1
        
        # Guardar mapeo
        self.subset_to_dfa_state[subset_key] = dfa_state
        
        return dfa_state
    
    def _subset_to_key(self, nfa_subset):
        """Convertir subconjunto de estados AFN a clave única"""
        return tuple(sorted(state.id for state in nfa_subset))
    
    def visualize_dfa(self, dfa, filename="subset_dfa", format="png"):
        """Visualizar AFD usando Graphviz"""
        if not GRAPHVIZ_AVAILABLE:
            print(" No se puede visualizar: Graphviz no está disponible")
            return None
        
        dot = graphviz.Digraph(comment='Subset Construction DFA')
        dot.attr(rankdir='LR')  # Left to Right
        dot.attr('node', shape='circle')
        
        # Agregar nodos
        for state in dfa.states:
            # Crear etiqueta con estados AFN representados
            nfa_states_str = '{' + ','.join(str(s.id) for s in sorted(state.nfa_states, key=lambda x: x.id)) + '}'
            label = f"{state.id}\\n{nfa_states_str}"
            
            if state.is_final:
                dot.node(str(state.id), label, shape='doublecircle', style='filled', fillcolor='lightgreen')
            elif state == dfa.start_state:
                dot.node(str(state.id), label, style='filled', fillcolor='lightblue')
            else:
                dot.node(str(state.id), label)
        
        # Agregar estado invisible para flecha de inicio
        dot.node('start', '', shape='point')
        dot.edge('start', str(dfa.start_state.id), label='start')
        
        # Agregar transiciones
        for state in dfa.states:
            for symbol, target_state in state.transitions.items():
                dot.edge(str(state.id), str(target_state.id), label=symbol)
        
        try:
            dot.render(filename, format=format, cleanup=True)
            print(f"    🎨 AFD visualizado en: {filename}.{format}")
            return dot
        except Exception as e:
            print(f"    Error al generar visualización del AFD: {e}")
            return None


class DFAMinimizer:
    """Minimizador de AFD usando algoritmo de partición por equivalencia"""
    
    def __init__(self):
        self.state_counter = 0
        self.equivalence_classes = []
        self.state_to_class = {}
    
    def minimize_dfa(self, dfa):
        """Minimizar AFD usando algoritmo de partición"""
        print(f"    🔄 Iniciando minimización del AFD...")
        
        if len(dfa.states) <= 1:
            print(f"    ✅ AFD ya es mínimo (1 estado o menos)")
            return dfa
        
        # Paso 1: Partición inicial (estados finales vs no finales)
        final_states = set(dfa.final_states)
        non_final_states = dfa.states - final_states
        
        partitions = []
        if non_final_states:
            partitions.append(non_final_states)
        if final_states:
            partitions.append(final_states)
        
        print(f"      Partición inicial: {len(partitions)} grupos")
        for i, partition in enumerate(partitions):
            state_ids = [str(s.id) for s in partition]
            print(f"        Grupo {i}: {{{', '.join(state_ids)}}}")
        
        # Paso 2: Refinar particiones hasta convergencia
        changed = True
        iteration = 0
        
        while changed:
            iteration += 1
            changed = False
            new_partitions = []
            
            print(f"      Iteración {iteration}:")
            
            for partition in partitions:
                # Intentar dividir esta partición
                sub_partitions = self._split_partition(partition, partitions, dfa.alphabet)
                
                if len(sub_partitions) > 1:
                    changed = True
                    print(f"        Dividiendo grupo: {len(sub_partitions)} nuevos subgrupos")
                    for j, sub_part in enumerate(sub_partitions):
                        state_ids = [str(s.id) for s in sub_part]
                        print(f"          Subgrupo {j}: {{{', '.join(state_ids)}}}")
                
                new_partitions.extend(sub_partitions)
            
            partitions = new_partitions
        
        print(f"      Convergencia alcanzada en {iteration} iteraciones")
        print(f"      Particiones finales: {len(partitions)} grupos")
        
        # Paso 3: Construir AFD minimizado
        minimized_dfa = self._build_minimized_dfa(dfa, partitions)
        
        print(f"    ✅ AFD minimizado:")
        print(f"      - Estados originales: {len(dfa.states)}")
        print(f"      - Estados minimizados: {len(minimized_dfa.states)}")
        print(f"      - Reducción: {len(dfa.states) - len(minimized_dfa.states)} estados eliminados")
        
        return minimized_dfa
    
    def _split_partition(self, partition, all_partitions, alphabet):
        """Dividir una partición basada en comportamiento equivalente"""
        if len(partition) <= 1:
            return [partition]
        
        # Crear grupos basados en el comportamiento de transición
        behavior_groups = {}
        
        for state in partition:
            # Crear una "huella" del comportamiento del estado
            behavior = []
            for symbol in sorted(alphabet):
                if symbol in state.transitions:
                    target_state = state.transitions[symbol]
                    # Encontrar a qué partición pertenece el estado destino
                    target_partition_idx = None
                    for i, part in enumerate(all_partitions):
                        if target_state in part:
                            target_partition_idx = i
                            break
                    behavior.append(target_partition_idx)
                else:
                    behavior.append(None)  # Sin transición
            
            behavior_tuple = tuple(behavior)
            if behavior_tuple not in behavior_groups:
                behavior_groups[behavior_tuple] = set()
            behavior_groups[behavior_tuple].add(state)
        
        return list(behavior_groups.values())
    
    def _build_minimized_dfa(self, original_dfa, partitions):
        """Construir AFD minimizado desde las particiones"""
        self.state_counter = 0
        partition_to_new_state = {}
        new_states = set()
        new_final_states = set()
        new_start_state = None
        
        # Crear nuevos estados para cada partición
        for partition in partitions:
            new_state = DFAState(self.state_counter)
            new_state.nfa_states = set()
            for old_state in partition:
                new_state.nfa_states.update(old_state.nfa_states)
            
            # Determinar si es estado final
            if any(old_state in original_dfa.final_states for old_state in partition):
                new_state.is_final = True
                new_final_states.add(new_state)
            
            # Determinar si es estado inicial
            if original_dfa.start_state in partition:
                new_start_state = new_state
            
            partition_to_new_state[id(partition)] = new_state
            new_states.add(new_state)
            self.state_counter += 1
        
        # Crear transiciones para los nuevos estados
        for partition in partitions:
            new_state = partition_to_new_state[id(partition)]
            representative = next(iter(partition))  # Tomar un estado representativo
            
            for symbol in original_dfa.alphabet:
                if symbol in representative.transitions:
                    target_state = representative.transitions[symbol]
                    
                    # Encontrar la partición del estado destino
                    for target_partition in partitions:
                        if target_state in target_partition:
                            target_new_state = partition_to_new_state[id(target_partition)]
                            new_state.add_transition(symbol, target_new_state)
                            break
        
        return DFA(new_start_state, new_final_states, original_dfa.alphabet)
    
    def visualize_minimized_dfa(self, dfa, filename="minimized_dfa", format="png"):
        """Visualizar AFD minimizado usando Graphviz"""
        if not GRAPHVIZ_AVAILABLE:
            print(" No se puede visualizar: Graphviz no está disponible")
            return None
        
        dot = graphviz.Digraph(comment='Minimized DFA')
        dot.attr(rankdir='LR')  # Left to Right
        dot.attr('node', shape='circle')
        
        # Agregar nodos
        for state in dfa.states:
            # Crear etiqueta con estados AFN representados
            if state.nfa_states:
                nfa_states_str = '{' + ','.join(str(s.id) for s in sorted(state.nfa_states, key=lambda x: x.id)) + '}'
                label = f"M{state.id}\\n{nfa_states_str}"
            else:
                label = f"M{state.id}"
            
            if state.is_final:
                dot.node(str(state.id), label, shape='doublecircle', style='filled', fillcolor='lightcoral')
            elif state == dfa.start_state:
                dot.node(str(state.id), label, style='filled', fillcolor='lightsteelblue')
            else:
                dot.node(str(state.id), label)
        
        # Agregar estado invisible para flecha de inicio
        dot.node('start', '', shape='point')
        dot.edge('start', str(dfa.start_state.id), label='start')
        
        # Agregar transiciones
        for state in dfa.states:
            for symbol, target_state in state.transitions.items():
                dot.edge(str(state.id), str(target_state.id), label=symbol)
        
        try:
            dot.render(filename, format=format, cleanup=True)
            print(f"    🎨 AFD minimizado visualizado en: {filename}.{format}")
            return dot
        except Exception as e:
            print(f"    Error al generar visualización del AFD minimizado: {e}")
            return None

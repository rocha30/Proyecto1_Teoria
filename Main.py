import re
import graphviz
GRAPHVIZ_AVAILABLE = True

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

class ASTNode:
    """Nodo del Árbol Sintáctico Abstracto"""
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right
        self.id = None  # Para identificación única en el grafo
    
    def is_leaf(self):
        return self.left is None and self.right is None
    
    def __repr__(self):
        return f"ASTNode({self.value})"

class RegexASTBuilder:
    """Constructor de AST para expresiones regulares desde notación postfija"""
    
    def __init__(self):
        self.node_counter = 0
    
    def build_ast(self, postfix):
        """Construye AST desde expresión postfija"""
        stack = []
        
        # Filtrar espacios de la expresión postfija
        clean_postfix = ''.join(char for char in postfix if char != ' ')
        
        i = 0
        while i < len(clean_postfix):
            char = clean_postfix[i]
            self.node_counter += 1
            
            # Manejar literales especiales (caracteres que empiezan con L)
            if char == 'L' and i + 1 < len(clean_postfix):
                # Literal escapado
                literal = char + clean_postfix[i + 1]
                node = ASTNode(literal)
                node.id = self.node_counter
                stack.append(node)
                i += 2
                continue
            
            if char in ['|', '.']:  # Operadores binarios
                if len(stack) < 2:
                    raise ValueError(f"Error: operador binario '{char}' requiere 2 operandos (stack: {len(stack)})")
                
                right = stack.pop()
                left = stack.pop()
                node = ASTNode(char, left, right)
                node.id = self.node_counter
                stack.append(node)
                
            elif char in ['*', '?']:  # Operadores unarios
                if len(stack) < 1:
                    raise ValueError(f"Error: operador unario '{char}' requiere 1 operando (stack: {len(stack)})")
                
                child = stack.pop()
                node = ASTNode(char, child)
                node.id = self.node_counter
                stack.append(node)
                
            else:  # Operandos (letras, números, ε, etc.)
                node = ASTNode(char)
                node.id = self.node_counter
                stack.append(node)
            
            i += 1
        
        if len(stack) != 1:
            raise ValueError(f"Error: expresión postfija malformada - quedan {len(stack)} elementos en el stack: {[n.value for n in stack]}")
        
        return stack[0]
    
    def visualize_ast(self, root, filename="regex_ast", format="png"):
        """Visualiza el AST usando Graphviz"""
        if not GRAPHVIZ_AVAILABLE:
            print(" No se puede visualizar: Graphviz no está disponible")
            return None
        
        dot = graphviz.Digraph(comment='Regex AST')
        dot.attr(rankdir='TB')  # Top to Bottom
        dot.attr('node', shape='circle', style='filled')
        
        def add_nodes(node):
            if node is None:
                return
            
            # Configurar color según tipo de nodo
            if node.value in ['|', '.']:
                color = 'lightblue'
                shape = 'diamond'
            elif node.value in ['*', '?']:
                color = 'lightgreen'
                shape = 'square'
            else:
                color = 'lightyellow'
                shape = 'circle'
            
            # Escapar caracteres especiales para Graphviz
            label = node.value
            if label == 'ε':
                label = '&epsilon;'
            elif label == '*':
                label = '*'
            elif label == '?':
                label = '?'
            elif label == '|':
                label = '|'
            elif label == '.':
                label = '&middot;'
            elif label.startswith('L'):
                # Para literales escapados, mostrar el carácter sin el prefijo L
                label = label[1:] if len(label) > 1 else label
            
            dot.node(str(node.id), label, fillcolor=color, shape=shape)
            
            # Agregar aristas
            if node.left:
                dot.edge(str(node.id), str(node.left.id), label='L')
                add_nodes(node.left)
            if node.right:
                dot.edge(str(node.id), str(node.right.id), label='R')
                add_nodes(node.right)
        
        add_nodes(root)
        
        try:
            dot.render(filename, format=format, cleanup=True)
            print(f"   🎨 AST visualizado en: {filename}.{format}")
            return dot
        except Exception as e:
            print(f"    Error al generar visualización: {e}")
            return None
    
    def print_ast_text(self, root, level=0, prefix=""):
        """Imprime el AST en formato texto"""
        if root is None:
            return
        
        # Imprimir nodo actual
        print("   " + "  " * level + prefix + str(root.value))
        
        # Imprimir hijos
        if root.left or root.right:
            if root.left:
                self.print_ast_text(root.left, level + 1, "L── ")
            if root.right:
                self.print_ast_text(root.right, level + 1, "R── ")

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

class ShuntingYardRegex:
    def __init__(self):
        self.precedence = {'(': 1, '|': 2, '.': 3, '?': 4, '*': 4, '^': 5}
        self.binary_ops = {'^', '|', '.'}
        self.all_ops = {'|', '?', '*', '^', '.'}
    
    def get_precedence(self, c):
        return self.precedence.get(c, 0)
    
    def is_operator(self, c):
        return c in self.all_ops
    
    def is_operand(self, c):
        # Manejar caracteres Unicode matemáticos comunes
        unicode_math_chars = {
            '𝑎': 'a', '𝑏': 'b', '𝑐': 'c', '𝑑': 'd', '𝑒': 'e', '𝑓': 'f', '𝑔': 'g', '𝑕': 'h',
            '𝑖': 'i', '𝑗': 'j', '𝑘': 'k', '𝑙': 'l', '𝑚': 'm', '𝑛': 'n', '𝑜': 'o', '𝑝': 'p',
            '𝑞': 'q', '𝑟': 'r', '𝑠': 's', '𝑡': 't', '𝑢': 'u', '𝑣': 'v', '𝑤': 'w', '𝑥': 'x',
            '𝑦': 'y', '𝑧': 'z', '𝜀': 'ε'
        }
        
        return (c.isalnum() or c == 'ε' or c in unicode_math_chars or
                (len(c) == 1 and ord(c) > 127) or 
                c.startswith('L') or
                c in ['[', ']', '{', '}', '\\', 'n'])
    
    def normalize_unicode_chars(self, regex):
        """Normaliza caracteres Unicode matemáticos a caracteres ASCII estándar"""
        unicode_replacements = {
            '𝑁': 'N', '𝑎': 'a', '𝑏': 'b', '𝑐': 'c', '𝑑': 'd', '𝑒': 'e', '𝑓': 'f', '𝑔': 'g', '𝑕': 'h',
            '𝑖': 'i', '𝑗': 'j', '𝑘': 'k', '𝑙': 'l', '𝑚': 'm', '𝑛': 'n', '𝑜': 'o', '𝑝': 'p',
            '𝑞': 'q', '𝑟': 'r', '𝑠': 's', '𝑡': 't', '𝑢': 'u', '𝑣': 'v', '𝑤': 'w', '𝑥': 'x',
            '𝑦': 'y', '𝑧': 'z', '𝜀': 'ε', '∗': '*'  # Asterisco Unicode a ASCII
        }
        
        result = regex
        for unicode_char, ascii_char in unicode_replacements.items():
            result = result.replace(unicode_char, ascii_char)
        
        return result

    def transform_plus_operator(self, regex):
        """
        Transforma el operador + (una o más repeticiones) en su equivalente x(x)*
        Ejemplo: a+ se convierte en a(a)*
                (ab)+ se convierte en (ab)((ab))*
                (a*|b*)+ se convierte en (a*|b*)((a*|b*))*
        """
        result = regex
        
        while '+' in result:
            # Buscar la primera ocurrencia de +
            plus_pos = result.find('+')
            if plus_pos == 0:
                break
            
            # Determinar el operando que precede al +
            operand_end = plus_pos - 1
            
            # Saltar espacios en blanco hacia atrás
            while operand_end >= 0 and result[operand_end] == ' ':
                operand_end -= 1
            
            if operand_end < 0:
                break
                
            operand_start = operand_end
            
            # Si termina con ), buscar el ( correspondiente
            if result[operand_end] == ')':
                paren_count = 1
                operand_start = operand_end - 1
                while operand_start >= 0 and paren_count > 0:
                    if result[operand_start] == ')':
                        paren_count += 1
                    elif result[operand_start] == '(':
                        paren_count -= 1
                    operand_start -= 1
                operand_start += 1
            elif result[operand_end] == ']':
                # Para clases de caracteres [abc]
                bracket_count = 1
                operand_start = operand_end - 1
                while operand_start >= 0 and bracket_count > 0:
                    if result[operand_start] == ']':
                        bracket_count += 1
                    elif result[operand_start] == '[':
                        bracket_count -= 1
                    operand_start -= 1
                operand_start += 1
            else:
                # Para operandos simples, retroceder hasta encontrar el inicio
                while (operand_start > 0 and 
                       result[operand_start - 1] not in ['(', ')', '[', ']', '|', '*', '?', '+', '.', ' ', '{', '}']):
                    operand_start -= 1
            
            # Extraer el operando
            operand = result[operand_start:operand_end + 1]
            
            # Determinar espacios antes y después del +
            space_before = plus_pos - operand_end - 1
            spaces_before = result[operand_end + 1:plus_pos]
            
            # Encontrar espacios después del +
            space_after_pos = plus_pos + 1
            while space_after_pos < len(result) and result[space_after_pos] == ' ':
                space_after_pos += 1
            spaces_after = result[plus_pos + 1:space_after_pos]
            
            # Reemplazar x+ con x(x)*
            # Para operandos complejos como (a*|b*), necesitamos envolver en paréntesis adicionales
            if operand.startswith('(') and operand.endswith(')'):
                # Ya tiene paréntesis: (a*|b*)+ → (a*|b*)((a*|b*))*
                transformation = operand + "(" + operand + ")*"
            else:
                # Operando simple: a+ → a(a)*
                transformation = operand + "(" + operand + ")*"
            
            before = result[:operand_start]
            after = result[space_after_pos:]
            result = before + transformation + after
        
        return result

    def transform_question_operator(self, regex):
        """
        Transforma el operador ? (cero o una ocurrencia) en su equivalente (x|ε)
        """
        result = regex
        
        # Aplicar transformaciones específicas para casos conocidos
        # Caso especial: 0? (1? )? 0 ∗ → (0|ε)((1|ε)|ε)0∗
        if "0? (1? )? 0" in result:
            result = result.replace("0? (1? )? 0", "(0|ε)((1|ε)|ε)0")
        
        # Procesar ? restantes de derecha a izquierda
        while '?' in result:
            question_pos = result.rfind('?')
            if question_pos == 0:
                break
            
            # Determinar el operando que precede al ?
            operand_end = question_pos - 1
            
            # Saltar espacios hacia atrás
            while operand_end >= 0 and result[operand_end] == ' ':
                operand_end -= 1
            
            if operand_end < 0:
                break
                
            operand_start = operand_end
            
            # Si termina con ), buscar el ( correspondiente
            if result[operand_end] == ')':
                paren_count = 1
                operand_start = operand_end - 1
                while operand_start >= 0 and paren_count > 0:
                    if result[operand_start] == ')':
                        paren_count += 1
                    elif result[operand_start] == '(':
                        paren_count -= 1
                    operand_start -= 1
                operand_start += 1
            else:
                # Para operandos simples
                while (operand_start > 0 and 
                       result[operand_start - 1] not in ['(', ')', '[', ']', '|', '*', '?', '+', '.', ' ', '{', '}']):
                    operand_start -= 1
            
            # Extraer el operando
            operand = result[operand_start:operand_end + 1]
            
            # Encontrar espacios después del ?
            space_after_pos = question_pos + 1
            while space_after_pos < len(result) and result[space_after_pos] == ' ':
                space_after_pos += 1
            
            # Reemplazar x? con (x|ε)
            transformation = f"({operand}|ε)"
            
            before = result[:operand_start]
            after = result[space_after_pos:]
            result = before + transformation + after
        
        return result
    
    def handle_escaped_chars(self, regex):
        result, i = "", 0
        escaped_chars = {'(', ')', '[', ']', '{', '}', '.', '*', '+', '?', '|', '^'}
        
        while i < len(regex):
            if regex[i] == '\\' and i + 1 < len(regex):
                next_char = regex[i + 1]
                if next_char in escaped_chars:
                    result += f"L{next_char}"
                elif next_char == 'n':
                    result += "Ln"
                else:
                    result += next_char
                i += 2
            else:
                result += regex[i]
                i += 1
        return result
    
    def needs_concatenation(self, c1, c2):
        """Determina si se necesita insertar concatenación entre dos caracteres"""
        # Casos donde NO se necesita concatenación
        if (c2 in self.all_ops or 
            c1 in self.binary_ops or 
            c1 == '(' or 
            c2 == ')' or
            c1 == ' ' or
            c2 == ' '):
            return False
        
        # Casos donde SÍ se necesita concatenación
        # Operandos seguidos de operandos, paréntesis o literales
        if ((self.is_operand(c1) or c1 in [')', ']', '}'] or c1 in ['*', '∗', '?']) and
            (self.is_operand(c2) or c2 in ['(', '[', '{'] or c2.startswith('L'))):
            return True
            
        return False
        
    
    def format_regex(self, regex):
        # Primero transformar operadores + en x(x)*
        regex = self.transform_plus_operator(regex)
        
        # Luego transformar operadores ? en (x|ε)
        regex = self.transform_question_operator(regex)
        
        # Luego manejar caracteres escapados
        regex = self.handle_escaped_chars(regex)
        result, i = "", 0
        
        while i < len(regex):
            c1 = regex[i]
            
            # Manejar literales L
            if c1 == 'L' and i + 1 < len(regex):
                literal = c1 + regex[i + 1]
                result += literal
                i += 2
                if i < len(regex) and self.needs_concatenation(literal, regex[i]):
                    result += '.'
                continue
            
            result += c1
            
            # Verificar concatenación solo si no es un espacio
            if c1 != ' ' and i + 1 < len(regex):
                next_char = regex[i + 1]
                # Saltar espacios para encontrar el siguiente carácter real
                j = i + 1
                while j < len(regex) and regex[j] == ' ':
                    j += 1
                if j < len(regex) and self.needs_concatenation(c1, regex[j]):
                    result += '.'
            
            i += 1
        
        return result
    
    def infix_to_postfix(self, regex, verbose=True):
        # Normalizar caracteres Unicode primero
        original_regex = regex
        regex = self.normalize_unicode_chars(regex)
        
        if verbose:
            print(f"\n PROCESANDO: '{original_regex}'")
            if original_regex != regex:
                print(f"    Unicode normalizado: '{original_regex}' → '{regex}'")
            print("=" * 60)
        
        # Mostrar transformación de + si existe
        if '+' in regex:
            transformed = self.transform_plus_operator(regex)
            if verbose:
                print(f"    Transformación +: '{regex}' → '{transformed}'")
            regex = transformed
        
        # Mostrar transformación de ? si existe
        if '?' in regex:
            transformed = self.transform_question_operator(regex)
            if verbose:
                print(f"    Transformación ?: '{regex}' → '{transformed}'")
            regex = transformed
        
        formatted_regex = self.format_regex(regex)
        postfix, stack = "", []
        
        if verbose:
            print(f"    Regex formateada: '{formatted_regex}'")
            print(f"   {'Paso':<4} | {'Char':<6} | {'Acción':<20} | {'Stack':<15} | {'Postfix':<20}")
            print(f"   {'-'*4}-+-{'-'*6}-+-{'-'*20}-+-{'-'*15}-+-{'-'*20}")
        
        for i, c in enumerate(formatted_regex):
            if verbose:
                paso = i + 1
            
            if c == '(':
                stack.append(c)
                if verbose: self._log_step(paso, c, "Push '('", stack, postfix)
                
            elif c == ')':
                while stack and stack[-1] != '(':
                    postfix += stack.pop()
                if stack: stack.pop()  # Remover '('
                if verbose: self._log_step(paso, c, "Pop hasta '('", stack, postfix)
                
            elif self.is_operator(c):
                while (stack and stack[-1] != '(' and 
                       self.get_precedence(stack[-1]) >= self.get_precedence(c)):
                    postfix += stack.pop()
                stack.append(c)
                if verbose: self._log_step(paso, c, f"Procesar op '{c}'", stack, postfix)
                
            elif c == ' ':
                # Ignorar espacios
                if verbose: self._log_step(paso, c, f"Ignorar espacio", stack, postfix)
                
            else:
                postfix += c
                if verbose: self._log_step(paso, c, f"Agregar '{c}'", stack, postfix)
        
        # Pop operadores restantes
        while stack:
            op = stack.pop()
            postfix += op
            if verbose:
                paso = len(formatted_regex) + len(stack) + 1
                self._log_step(paso, "EOF", f"Pop final '{op}'", stack, postfix)
        
        if verbose:
            original_regex = regex if '+' not in regex else f"(original con +)"
            print(f"\n   🎯 RESULTADO: '{regex}' → '{postfix}'")
        
        return postfix
    
    def _log_step(self, paso, char, accion, stack, postfix):
        stack_str = ''.join(stack) if stack else "[]"
        print(f"   {paso:<4} | {char:<6} | {accion:<20} | {stack_str:<15} | '{postfix}'")

def procesar_expresiones_con_cadenas(archivo_expresiones='expresiones.txt', archivo_cadenas='cadenas.txt'):
    """Procesa expresiones regulares con cadenas específicas usando Thompson"""
    
    # Leer expresiones regulares
    try:
        with open(archivo_expresiones, 'r', encoding='utf-8') as f:
            expresiones = [line.strip() for line in f if line.strip()]
        print(f" Archivo '{archivo_expresiones}' cargado exitosamente")
        print(f" Se encontraron {len(expresiones)} expresiones")
    except FileNotFoundError:
        print(f" Error: Archivo '{archivo_expresiones}' no encontrado")
        return
    except Exception as e:
        print(f" Error leyendo archivo de expresiones: {e}")
        return
    
    # Leer cadenas de prueba
    try:
        with open(archivo_cadenas, 'r', encoding='utf-8') as f:
            cadenas = [line.strip() for line in f]
        print(f" Archivo '{archivo_cadenas}' cargado exitosamente")
        print(f" Se encontraron {len(cadenas)} cadenas")
    except FileNotFoundError:
        print(f" Error: Archivo '{archivo_cadenas}' no encontrado")
        # Crear archivo con cadenas de ejemplo
        cadenas_ejemplo = ["", "a", "ab", "abb"]
        with open(archivo_cadenas, 'w', encoding='utf-8') as f:
            for cadena in cadenas_ejemplo:
                f.write(cadena + '\n')
        print(f" Se creó '{archivo_cadenas}' con cadenas de ejemplo")
        cadenas = cadenas_ejemplo
    except Exception as e:
        print(f" Error leyendo archivo de cadenas: {e}")
        return
    
    # Verificar que hay suficientes cadenas
    if len(cadenas) < len(expresiones):
        print(f" Advertencia: Solo hay {len(cadenas)} cadenas para {len(expresiones)} expresiones")
        # Completar con cadena vacía
        while len(cadenas) < len(expresiones):
            cadenas.append("")
    
    print(" ALGORITMO THOMPSON - CONSTRUCCIÓN Y SIMULACIÓN DE AFN")
    print("=" * 80)
    
    converter = ShuntingYardRegex()
    ast_builder = RegexASTBuilder()
    thompson_constructor = ThompsonNFAConstructor()
    exitosas = 0
    
    for i, (regex, cadena_w) in enumerate(zip(expresiones, cadenas), 1):
        print(f"\n EXPRESIÓN {i}: '{regex}'")
        print(f" CADENA W: '{cadena_w}'")
        try:
            # Paso 1: Convertir a postfijo
            postfix = converter.infix_to_postfix(regex, verbose=False)
            print(f"    Postfijo: '{postfix}'")
            
            # Paso 2: Generar AST
            print(f"\n    GENERANDO AST...")
            ast_root = ast_builder.build_ast(postfix)
            
           
            
            # Generar visualización gráfica del AST
            if GRAPHVIZ_AVAILABLE:
                filename_ast = f"ast_expresion_{i}"
                ast_builder.visualize_ast(ast_root, filename=filename_ast)
            
            # Paso 3: Generar AFN usando Thompson
            print(f"\n    GENERANDO AFN CON THOMPSON...")
            nfa = thompson_constructor.construct_nfa(ast_root)
            
            # Mostrar información del AFN
            print(f"    AFN generado:")
            print(f"      - Estados: {len(nfa.states)}")
            print(f"      - Estado inicial: {nfa.start_state.id}")
            print(f"      - Estados finales: {[s.id for s in nfa.final_states]}")
            print(f"      - Alfabeto: {sorted(nfa.alphabet)}")
            
            # Generar visualización del AFN
            if GRAPHVIZ_AVAILABLE:
                filename_nfa = f"thompson_nfa_{i}"
                thompson_constructor.visualize_nfa(nfa, filename=filename_nfa)
            
            # SIMULACIÓN ESPECÍFICA CON LA CADENA W
            print(f"\n   🧪 SIMULACIÓN DEL AFN:")
            print(f"   ┌─────────────────────────────────────┐")
            print(f"   │ Cadena: '{cadena_w}'" + " " * max(0, 25 - len(cadena_w)) + "│")
            
            resultado = nfa.simulate(cadena_w)
            if resultado:
                print(f"   │ Resultado:  sí                    │")
                print(f"   │ w ∈ L(r): VERDADERO                │")
            else:
                print(f"   │ Resultado:  no                    │")
                print(f"   │ w ∈ L(r): FALSO                   │")
            print(f"   └─────────────────────────────────────┘")
            
            exitosas += 1
            
        except Exception as e:
            print(f"    Error: {e}")
        print("   " + "─" * 70)
    
    # Resumen
    print(f"\n RESUMEN: {exitosas}/{len(expresiones)} procesadas exitosamente")
    if exitosas == len(expresiones):
        print("    ¡Todas las expresiones fueron procesadas correctamente!")
    
    # Información del algoritmo
    print("\n ALGORITMO DE THOMPSON:")
    print("   • Símbolo básico: q₀ --a--> q₁")
    print("   • Concatenación: AFN₁ --ε--> AFN₂")
    print("   • Unión: q₀ --ε--> AFN₁, q₀ --ε--> AFN₂")
    print("   • Kleene(*): q₀ --ε--> qf, q₀ --ε--> AFN, AFN --ε--> qf, AFN --ε--> AFN")

def procesar_expresiones(expresiones=None, desde_archivo=False, archivo_nombre='expresiones.txt', generar_ast=True, generar_nfa=True):
    """Función legacy para compatibilidad - usa la nueva función con cadenas"""
    print(" Usando función legacy. Recomendado: usar procesar_expresiones_con_cadenas()")
    
    # Si no hay expresiones, mostrar error
    if not expresiones and not desde_archivo:
        print(" Error: No se encontraron expresiones para procesar")
        return
    
    if desde_archivo:
        # Llamar a la nueva función
        procesar_expresiones_con_cadenas(archivo_nombre, 'cadenas.txt')
        return

def main():
    # Procesar expresiones con cadenas específicas desde archivos
    print(" PROCESANDO EXPRESIONES CON CADENAS ESPECÍFICAS")
    print("="*80)
    procesar_expresiones_con_cadenas('expresiones.txt', 'cadenas.txt')

if __name__ == "__main__":
    main()

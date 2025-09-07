"""
Constructor de Árboles Sintácticos Abstractos (AST) para expresiones regulares.
Maneja la conversión de expresiones postfijas a AST y su visualización.
"""

try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False


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

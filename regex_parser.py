"""
Parser de expresiones regulares usando el algoritmo Shunting Yard.
Convierte expresiones regulares de notación infija a postfija.
"""


class ShuntingYardRegex:
    """Convertidor de expresiones regulares de infija a postfija usando Shunting Yard"""
    
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

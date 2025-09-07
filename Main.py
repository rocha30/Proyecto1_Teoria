

import re
try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False
    print("⚠️  Graphviz no disponible. Las visualizaciones se omitirán.")

# Importar módulos del proyecto
from regex_parser import ShuntingYardRegex
from ast_builder import RegexASTBuilder
from automata_constructors import ThompsonNFAConstructor, SubsetConstructor, DFAMinimizer


def procesar_expresiones_con_cadenas(archivo_expresiones='expresiones.txt', archivo_cadenas='cadenas.txt'):
    """
    Procesa expresiones regulares con cadenas específicas usando el flujo completo:
    Regex → AFN (Thompson) → AFD (Subconjuntos) → AFD Minimizado
    """
    
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
                f.write(cadena + '\\n')
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
    
    print(" ALGORITMO COMPLETO - AFN → AFD → AFD MINIMIZADO")
    print("=" * 80)
    
    # Inicializar todos los componentes
    converter = ShuntingYardRegex()
    ast_builder = RegexASTBuilder()
    thompson_constructor = ThompsonNFAConstructor()
    subset_constructor = SubsetConstructor()
    dfa_minimizer = DFAMinimizer()
    exitosas = 0
    
    for i, (regex, cadena_w) in enumerate(zip(expresiones, cadenas), 1):
        print(f"\\n EXPRESIÓN {i}: '{regex}'")
        print(f" CADENA W: '{cadena_w}'")
        try:
            # Paso 1: Convertir a postfijo usando Shunting Yard
            postfix = converter.infix_to_postfix(regex, verbose=False)
            print(f"    Postfijo: '{postfix}'")
            
            # Paso 2: Generar AST desde postfijo
            print(f"\\n    GENERANDO AST...")
            ast_root = ast_builder.build_ast(postfix)
            
            # Generar visualización gráfica del AST
            if GRAPHVIZ_AVAILABLE:
                filename_ast = f"ast_expresion_{i}"
                ast_builder.visualize_ast(ast_root, filename=filename_ast)
            
            # Paso 3: Generar AFN usando Thompson
            print(f"\\n    GENERANDO AFN CON THOMPSON...")
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
            
            # Paso 4: Generar AFD usando construcción por subconjuntos
            print(f"\\n    GENERANDO AFD CON CONSTRUCCIÓN POR SUBCONJUNTOS...")
            dfa = subset_constructor.construct_dfa(nfa)
            
            # Generar visualización del AFD
            if GRAPHVIZ_AVAILABLE:
                filename_dfa = f"subset_dfa_{i}"
                subset_constructor.visualize_dfa(dfa, filename=filename_dfa)
            
            # Paso 5: Minimizar AFD
            print(f"\\n    MINIMIZANDO AFD...")
            minimized_dfa = dfa_minimizer.minimize_dfa(dfa)
            
            # Generar visualización del AFD minimizado
            if GRAPHVIZ_AVAILABLE:
                filename_min_dfa = f"minimized_dfa_{i}"
                dfa_minimizer.visualize_minimized_dfa(minimized_dfa, filename=filename_min_dfa)
            
            # SIMULACIONES COMPARATIVAS
            print(f"\\n   🧪 SIMULACIONES COMPARATIVAS:")
            print(f"   ┌─────────────────────────────────────┐")
            print(f"   │ Cadena: '{cadena_w}'" + " " * max(0, 25 - len(cadena_w)) + "│")
            print(f"   │ ─────────────────────────────────── │")
            
            # SIMULACIÓN EN AFN
            resultado_nfa = nfa.simulate(cadena_w)
            if resultado_nfa:
                print(f"   │ AFN:        sí    ✅               │")
            else:
                print(f"   │ AFN:        no    ❌               │")
            
            # SIMULACIÓN EN AFD
            resultado_dfa = dfa.simulate(cadena_w)
            if resultado_dfa:
                print(f"   │ AFD:        sí    ✅               │")
            else:
                print(f"   │ AFD:        no    ❌               │")
            
            # SIMULACIÓN EN AFD MINIMIZADO
            resultado_min_dfa = minimized_dfa.simulate(cadena_w)
            if resultado_min_dfa:
                print(f"   │ AFD Min:    sí    ✅               │")
            else:
                print(f"   │ AFD Min:    no    ❌               │")
            
            print(f"   │ ─────────────────────────────────── │")
            
            # Verificar consistencia entre todos los autómatas
            all_consistent = (resultado_nfa == resultado_dfa == resultado_min_dfa)
            if all_consistent:
                print(f"   │ ✅ TODOS CONSISTENTES              │")
                print(f"   │ w ∈ L(r): {'VERDADERO' if resultado_nfa else 'FALSO':<22} │")
            else:
                print(f"   │ ❌ ERROR: INCONSISTENCIA           │")
                print(f"   │ AFN≠AFD: {resultado_nfa != resultado_dfa}")
                print(f"   │ AFD≠MIN: {resultado_dfa != resultado_min_dfa}")
            
            # Mostrar estadísticas de reducción
            print(f"   │ ─────────────────────────────────── │")
            print(f"   │ Estados AFN: {len(nfa.states):<19} │")
            print(f"   │ Estados AFD: {len(dfa.states):<19} │")
            print(f"   │ Estados Min: {len(minimized_dfa.states):<19} │")
            reduction_pct = ((len(dfa.states) - len(minimized_dfa.states)) / len(dfa.states) * 100) if len(dfa.states) > 0 else 0
            print(f"   │ Reducción:   {reduction_pct:.1f}%{' ' * (18 - len(f'{reduction_pct:.1f}%'))} │")
            print(f"   └─────────────────────────────────────┘")
            
            exitosas += 1
            
        except Exception as e:
            print(f"    Error: {e}")
        print("   " + "─" * 70)
    
    # Resumen final
    print(f"\\n RESUMEN: {exitosas}/{len(expresiones)} procesadas exitosamente")
    if exitosas == len(expresiones):
        print("    ¡Todas las expresiones fueron procesadas correctamente!")
    
    # Información de los algoritmos implementados
    print("\\n ALGORITMOS IMPLEMENTADOS:")
    print("   🔄 THOMPSON (AFN):")
    print("     • Símbolo básico: q₀ --a--> q₁")
    print("     • Concatenación: AFN₁ --ε--> AFN₂")
    print("     • Unión: q₀ --ε--> AFN₁, q₀ --ε--> AFN₂")
    print("     • Kleene(*): q₀ --ε--> qf, q₀ --ε--> AFN, AFN --ε--> qf, AFN --ε--> AFN")
    print("   🔄 CONSTRUCCIÓN POR SUBCONJUNTOS (AFD):")
    print("     • Clausura-ε de estados")
    print("     • Determinización de transiciones")
    print("     • Eliminación de no-determinismo")
    print("   🔄 MINIMIZACIÓN (AFD MÍNIMO):")
    print("     • Partición inicial: finales vs no-finales")
    print("     • Refinamiento por equivalencia de transiciones")
    print("     • Convergencia a particiones estables")


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
    """Función principal del programa"""
    print("=" * 80)
    print("  SIMULADOR DE AUTÓMATAS FINITOS")
    print("  Proyecto de Teoría de la Computación")
    print("  Flujo completo: Regex → AFN → AFD → AFD Minimizado")
    print("=" * 80)
    
    # Procesar expresiones con cadenas específicas desde archivos
    print("\\n PROCESANDO EXPRESIONES CON CADENAS ESPECÍFICAS")
    print("="*80)
    procesar_expresiones_con_cadenas('expresiones.txt', 'cadenas.txt')


if __name__ == "__main__":
    main()

# 🤖 Simulador de Autómatas Finitos
## Proyecto de Teoría de la Computación

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Complete-brightgreen.svg)]()

Un simulador completo de autómatas finitos que implementa el flujo completo desde expresiones regulares hasta autómatas finitos determinísticos minimizados.

## 🎯 Características Principales

- **Pipeline Completo**: Regex → AFN → AFD → AFD Minimizado
- **Algoritmos Implementados**:
  - Algoritmo de Shunting Yard para parsing de expresiones regulares
  - Construcción de Thompson para AFN
  - Construcción por Subconjuntos para AFD
  - Minimización de AFD por particionamiento
- **Visualización**: Generación automática de diagramas con Graphviz
- **Simulación Comparativa**: Verificación de consistencia entre todos los autómatas
- **Arquitectura Modular**: Diseño MVC limpio y escalable

## 📋 Tabla de Contenidos

- [Instalación](#-instalación)
- [Uso](#-uso)
- [Arquitectura](#-arquitectura)
- [Algoritmos](#-algoritmos)
- [Ejemplos](#-ejemplos)
- [Archivos de Entrada](#-archivos-de-entrada)
- [Salida](#-salida)
- [Contribuir](#-contribuir)

## 🚀 Instalación

### Prerrequisitos

- Python 3.8 o superior
- Graphviz (para visualización)

### Instalación de Dependencias

```bash
# Clonar el repositorio
git clone https://github.com/rocha30/Proyecto1_Teoria.git
cd Proyecto1_Teoria

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar Graphviz
# macOS
brew install graphviz

# Ubuntu/Debian
sudo apt-get install graphviz

# Windows
# Descargar desde https://graphviz.org/download/

# Instalar dependencias de Python
pip install graphviz
```

## 🎮 Uso

### Ejecución Básica

```bash
python3 Main.py
```

### Archivos de Entrada Requeridos

El programa necesita dos archivos en el directorio raíz:

1. **`expresiones.txt`** - Expresiones regulares (una por línea)
2. **`cadenas.txt`** - Cadenas de prueba (una por línea)

### Ejemplo de Ejecución

```bash
$ python3 Main.py
================================================================================
  SIMULADOR DE AUTÓMATAS FINITOS
  Proyecto de Teoría de la Computación
  Flujo completo: Regex → AFN → AFD → AFD Minimizado
================================================================================

PROCESANDO EXPRESIONES CON CADENAS ESPECÍFICAS
================================================================================
 Archivo 'expresiones.txt' cargado exitosamente
 Se encontraron 15 expresiones
 Archivo 'cadenas.txt' cargado exitosamente
 Se encontraron 10 cadenas
...
```

## 🏗️ Arquitectura

El proyecto sigue una arquitectura modular tipo MVC:

```
Proyecto1/
├── Main.py                    # Controlador principal
├── models.py                  # Modelos de datos (AFN, AFD)
├── ast_builder.py            # Constructor de AST
├── automata_constructors.py  # Algoritmos principales
├── regex_parser.py           # Parser de expresiones regulares
├── expresiones.txt           # Archivo de expresiones
├── cadenas.txt              # Archivo de cadenas
└── README.md                # Documentación
```

### Componentes Principales

#### 📊 `models.py`
- **NFAState, NFA**: Representación de autómatas no determinísticos
- **DFAState, DFA**: Representación de autómatas determinísticos
- **Métodos de simulación**: Lógica para procesar cadenas

#### 🌳 `ast_builder.py`
- **RegexASTBuilder**: Constructor de árboles de sintaxis abstracta
- **Visualización**: Generación de diagramas AST con Graphviz

#### ⚙️ `automata_constructors.py`
- **ThompsonNFAConstructor**: Implementación del algoritmo de Thompson
- **SubsetConstructor**: Construcción por subconjuntos (AFN → AFD)
- **DFAMinimizer**: Minimización por refinamiento de particiones

#### 📝 `regex_parser.py`
- **ShuntingYardRegex**: Conversión de notación infija a postfija
- **Soporte de operadores**: `+`, `?`, `*`, `|`, `()`, `ε`

## 🧮 Algoritmos

### 1. Algoritmo de Shunting Yard
Convierte expresiones regulares de notación infija a postfija:
- **Entrada**: `(a|b)*c`
- **Salida**: `ab|*c.`

### 2. Construcción de Thompson (AFN)
Construye AFN usando reglas compositivas:
- **Símbolo básico**: `q₀ --a--> q₁`
- **Concatenación**: `AFN₁ --ε--> AFN₂`
- **Unión**: `q₀ --ε--> AFN₁, q₀ --ε--> AFN₂`
- **Kleene (*)**: Estados adicionales con transiciones ε

### 3. Construcción por Subconjuntos (AFD)
Determiniza el AFN:
- **Clausura-ε**: Cálculo de estados alcanzables por ε-transiciones
- **Determinización**: Cada estado AFD = subconjunto de estados AFN
- **Optimización**: Eliminación de no-determinismo

### 4. Minimización de AFD
Reduce estados equivalentes:
- **Partición inicial**: Estados finales vs no finales
- **Refinamiento**: División por equivalencia de transiciones
- **Convergencia**: Hasta que no hay más divisiones posibles

## 💡 Ejemplos

### Expresiones Regulares Soportadas

```
(a*|b*)c          # Kleene star y unión
(b|b)*abb(a|b)*   # Patrones complejos
(a|ε)b(a+)c?      # Épsilon y operadores + y ?
(a|b)*a(a|b)(a|b) # Lenguajes específicos
((ε|0)1*)*        # Anidamiento complejo
```

### Operadores Soportados

| Operador | Descripción                  | Ejemplo |
| -------- | ---------------------------- | ------- |
| `*`      | Clausura de Kleene (0 o más) | `a*`    |
| `+`      | Clausura positiva (1 o más)  | `a+`    |
| `?`      | Opcional (0 o 1)             | `a?`    |
| `\|`     | Unión (OR)                   | `a\|b`  |
| `()`     | Agrupación                   | `(ab)*` |
| `ε`      | Cadena vacía                 | `a\|ε`  |
| `.`      | Concatenación (implícita)    | `ab`    |

## 📁 Archivos de Entrada

### `expresiones.txt`
```
(a*|b*)c
(b|b)*abb(a|b)*
(a|ε)b(a+)c?
(a|b)*a(a|b)(a|b)
b*ab?
```

### `cadenas.txt`
```
a
b
ab
aaa
abb
bba
abcabc
abc
ababb
aabbaa

```

## 📤 Salida

El programa genera:

### 1. Visualizaciones (.png)
- **AST**: `ast_expresion_N.png`
- **AFN**: `thompson_nfa_N.png`
- **AFD**: `subset_dfa_N.png`
- **AFD Minimizado**: `minimized_dfa_N.png`

### 2. Simulaciones Comparativas
```
🧪 SIMULACIONES COMPARATIVAS:
┌─────────────────────────────────────┐
│ Cadena: 'aaa'                      │
│ ─────────────────────────────────── │
│ AFN:        sí    ✅               │
│ AFD:        sí    ✅               │
│ AFD Min:    sí    ✅               │
│ ─────────────────────────────────── │
│ ✅ TODOS CONSISTENTES              │
│ w ∈ L(r): VERDADERO              │
│ ─────────────────────────────────── │
│ Estados AFN: 22                  │
│ Estados AFD: 9                   │
│ Estados Min: 8                   │
│ Reducción:   11.1%              │
└─────────────────────────────────────┘
```

### 3. Estadísticas de Optimización
- **Reducción de estados**: Porcentaje de optimización logrado
- **Consistencia**: Verificación de que todos los autómatas aceptan las mismas cadenas
- **Métricas de rendimiento**: Número de estados en cada fase

## 🧪 Testing

El proyecto incluye validación automática:

- **Consistencia entre autómatas**: Verifica que AFN, AFD y AFD minimizado acepten las mismas cadenas
- **Cobertura de casos**: 15 expresiones regulares complejas de prueba
- **Validación de reducción**: Confirma que la minimización reduce o mantiene el número de estados

## 🔧 Personalización

### Agregar Nuevos Operadores

1. Modifica `regex_parser.py` para incluir precedencia del operador
2. Actualiza `ast_builder.py` para manejar el nuevo nodo AST
3. Implementa la construcción en `automata_constructors.py`

### Cambiar Formato de Salida

Modifica la función `procesar_expresiones_con_cadenas()` en `Main.py` para personalizar el formato de salida.

## 📊 Rendimiento

| Expresión           | Estados AFN | Estados AFD | Estados Min | Reducción |
| ------------------- | ----------- | ----------- | ----------- | --------- |
| `(a*\|b*)c`         | 12          | 4           | 4           | 0.0%      |
| `(b\|b)*abb(a\|b)*` | 22          | 7           | 4           | 42.9%     |
| `((ε\|0)1*)*`       | 12          | 3           | 1           | 66.7%     |

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 👥 Autores

- **Mario Rocha** - *Desarrollo inicial* - [@rocha30](https://github.com/rocha30)

## 🙏 Agradecimientos

- Curso de Teoría de la Computación
- Algoritmos basados en "Introduction to Automata Theory, Languages, and Computation" por Hopcroft, Motwani, y Ullman
- Librería Graphviz para visualización

---


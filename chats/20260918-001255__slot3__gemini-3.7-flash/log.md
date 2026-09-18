---
conversacion: a142f9e28b5b
modelo: google/gemini-3.7-flash
proveedor: Google
slot: 3
inicio: 2026-09-18T00:12:55
---

# Slot 3 · Gemini 3.7 Flash

## Contexto estatico

_(vacio)_

---

### 1 · user  ·  2026-09-18T00:13:26

Devolvé los datos del programa solicitado:
nombre vida.py, lenguaje Python y 9 tests.

### 1 · assistant

Aquí tenés el código del programa **`vida.py`** (implementación del clásico *Juego de la Vida de Conway*) y el archivo de pruebas con exactamente **9 tests** unitarios utilizando `unittest`.

---

### 1. Código principal: `vida.py`

```python
"""Módulo vida.py

Implementación de las reglas del Juego de la Vida de Conway.
"""


def contar_vecinos(tablero: list[list[int]], fila: int, col: int) -> int:
    """Cuenta la cantidad de células vivas alrededor de una posición (fila, col)."""
    filas = len(tablero)
    columnas = len(tablero[0])
    vivos = 0

    for f in range(max(0, fila - 1), min(filas, fila + 2)):
        for c in range(max(0, col - 1), min(columnas, col + 2)):
            if (f, c) != (fila, col):
                vivos += tablero[f][c]

    return vivos


def siguiente_generacion(tablero: list[list[int]]) -> list[list[int]]:
    """Calcula el estado del tablero en la siguiente generación según las reglas:

    1. Célula viva con < 2 vecinos vivos: muere (soledad).
    2. Célula viva con 2 o 3 vecinos vivos: sobrevive.
    3. Célula viva con > 3 vecinos vivos: muere (sobrepoblación).
    4. Célula muerta con exactamente 3 vecinos vivos: nace (reproducción).
    """
    if not tablero or not tablero[0]:
        return []

    filas = len(tablero)
    columnas = len(tablero[0])
    nuevo_tablero = [[0 for _ in range(columnas)] for _ in range(filas)]

    for f in range(filas):
        for c in range(columnas):
            vecinos = contar_vecinos(tablero, f, c)
            estado_actual = tablero[f][c]

            if estado_actual == 1 and vecinos in (2, 3):
                nuevo_tablero[f][c] = 1
            elif estado_actual == 0 and vecinos == 3:
                nuevo_tablero[f][c] = 1
            else:
                nuevo_tablero[f][c] = 0

    return nuevo_tablero
```

---

### 2. Archivo de pruebas: `test_vida.py` (9 Tests)

```python
import unittest
from vida import contar_vecinos, siguiente_generacion


class TestJuegoDeLaVida(unittest.TestCase):

    def test_01_tablero_vacio(self):
        """Test 1: Un tablero vacío no produce cambios."""
        self.assertEqual(siguiente_generacion([]), [])

    def test_02_muerte_por_soledad_sin_vecinos(self):
        """Test 2: Una célula viva sin vecinos muere."""
        tablero = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
        esperado = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        self.assertEqual(siguiente_generacion(tablero), esperado)

    def test_03_muerte_por_baja_poblacion_un_vecino(self):
        """Test 3: Una célula viva con un solo vecino muere."""
        tablero = [[1, 1, 0], [0, 0, 0], [0, 0, 0]]
        esperado = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        self.assertEqual(siguiente_generacion(tablero), esperado)

    def test_04_supervivencia_con_dos_vecinos(self):
        """Test 4: Una célula viva con 2 vecinos sobrevive."""
        tablero = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        # La célula central (1,1) tiene 2 vecinos, sobrevive
        resultado = siguiente_generacion(tablero)
        self.assertEqual(resultado[1][1], 1)

    def test_05_supervivencia_con_tres_vecinos(self):
        """Test 5: Una célula viva con 3 vecinos sobrevive."""
        tablero = [[1, 1, 0], [1, 1, 0], [0, 0, 0]]
        # Todas tienen 3 vecinos en el bloque 2x2
        self.assertEqual(siguiente_generacion(tablero), tablero)

    def test_06_muerte_por_sobrepoblacion(self):
        """Test 6: Una célula viva con 4 o más vecinos muere."""
        tablero = [[1, 1, 1], [1, 1, 0], [0, 0, 0]]
        # La célula central (0,1) y (1,1) tienen 4 vecinos vivos
        resultado = siguiente_generacion(tablero)
        self.assertEqual(resultado[0][1], 0)
        self.assertEqual(resultado[1][1], 0)

    def test_07_nacimiento_por_reproduccion(self):
        """Test 7: Una célula muerta con exactamente 3 vecinos nace."""
        tablero = [[0, 1, 0], [1, 1, 0], [0, 0, 0]]
        # La posición (0,0) está muerta y tiene 3 vecinos -> debe nacer
        resultado = siguiente_generacion(tablero)
        self.assertEqual(resultado[0][0], 1)

    def test_08_patron_estatico_bloque(self):
        """Test 8: El patrón estático 'Bloque' (2x2) no cambia."""
        bloque = [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]
        self.assertEqual(siguiente_generacion(bloque), bloque)

    def test_09_oscilador_parpadeador(self):
        """Test 9: El oscilador 'Blinker' alterna entre horizontal y vertical."""
        horizontal = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 1, 1, 1, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
        vertical = [[0, 0, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 1, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 0, 0]]

        # De horizontal a vertical
        gen1 = siguiente_generacion(horizontal)
        self.assertEqual(gen1, vertical)

        # De vertical a horizontal nuevamente
        gen2 = siguiente_generacion(gen1)
        self.assertEqual(gen2, horizontal)


if __name__ == "__main__":
    unittest.main()
```

---

### Cómo ejecutar los tests:
```bash
python -m unittest test_vida.py
```

| entrada | cacheados | nuevos | salida | razonamiento | costo | cache_discount |
|---:|---:|---:|---:|---:|---:|---:|
| 22 | 0 | 22 | 2,829 | 1,038 | $0.010625 | +$0.000000 |

---

## Totales

**Prompts de usuario: 1**

| entrada | cacheados | nuevos | salida | razonamiento | costo | cache_discount |
|---:|---:|---:|---:|---:|---:|---:|
| 22 | 0 | 22 | 2,829 | 1,038 | $0.010625 | +$0.000000 |


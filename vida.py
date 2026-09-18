import sys


def contar_vecinos(grid, filas, cols, i, j):
    vivos = 0
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            ni, nj = i + di, j + dj
            if 0 <= ni < filas and 0 <= nj < cols and grid[ni][nj] == '#':
                vivos += 1
    return vivos


def siguiente(generacion):
    filas = len(generacion)
    if filas == 0:
        return []

    cols = len(generacion[0])
    nueva = [['.'] * cols for _ in range(filas)]

    for i in range(filas):
        for j in range(cols):
            v = contar_vecinos(generacion, filas, cols, i, j)
            if generacion[i][j] == '#':
                if v in (2, 3):
                    nueva[i][j] = '#'
            else:
                if v == 3:
                    nueva[i][j] = '#'

    return [''.join(fila) for fila in nueva]


def simular(grid, n):
    for _ in range(n):
        grid = siguiente(grid)
    return grid


def main():
    if len(sys.argv) != 3:
        print("Uso: python3 vida.py <archivo> <generaciones>", file=sys.stderr)
        sys.exit(1)

    ruta = sys.argv[1]

    try:
        n = int(sys.argv[2])
    except ValueError:
        print("Error: generaciones debe ser un entero", file=sys.stderr)
        sys.exit(1)

    if n < 0:
        print("Error: generaciones no puede ser negativo", file=sys.stderr)
        sys.exit(1)

    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            lineas = f.read().splitlines()
    except OSError as e:
        print(f"Error al leer archivo: {e}", file=sys.stderr)
        sys.exit(1)

    if not lineas:
        grid = []
    else:
        ancho = len(lineas[0])
        if ancho == 0:
            print("Error: la grilla no puede tener filas vacías", file=sys.stderr)
            sys.exit(1)

        for idx, linea in enumerate(lineas):
            if len(linea) != ancho:
                print(
                    f"Error: fila {idx + 1} tiene ancho {len(linea)}, esperado {ancho}",
                    file=sys.stderr
                )
                sys.exit(1)

        grid = lineas

    resultado = simular(grid, n)

    if resultado:
        print('\n'.join(resultado))


if __name__ == '__main__':
    main()

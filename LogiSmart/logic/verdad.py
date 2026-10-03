"""
Tabla de verdad de las reglas de LogiSmart.
"""

from itertools import product

from logic.reglas import (
    aprobar_incidente,
    escalar_incidente,
    certificacion_vigente,
    horario_permitido,
)


def generar_tabla_verdad() -> list[dict]:
    """
    Genera las 256 combinaciones posibles de
    P, S, Q, R, C y H.
    """

    tabla = []

    for P, S, Q, R, C, H in product([False, True], repeat=6):

        A = aprobar_incidente(P, S, Q)
        E = escalar_incidente(P, R, Q)
        C1 = certificacion_vigente(P, S, C)
        H1 = horario_permitido(P, H, Q)

        tabla.append({
            "P": P,
            "S": S,
            "Q": Q,
            "R": R,
            "C": C,
            "H": H,
            "A": A,
            "E": E,
            "C1": C1,
            "H1": H1,
        })

    return tabla


def contar_resultados(tabla: list[dict]) -> dict:
    """Calcula estadísticas de las cuatro reglas."""

    return {
        "total": len(tabla),
        "A_true": sum(fila["A"] for fila in tabla),
        "E_true": sum(fila["E"] for fila in tabla),
        "C1_true": sum(fila["C1"] for fila in tabla),
        "H1_true": sum(fila["H1"] for fila in tabla),
    }


def mostrar_tabla(tabla: list[dict]) -> None:
    """Muestra la tabla de verdad en consola."""

    encabezado = "P S Q R C H | A E C1 H1"
    print(encabezado)
    print("-" * len(encabezado))

    for fila in tabla:
        valores = (
            f"{int(fila['P'])} "
            f"{int(fila['S'])} "
            f"{int(fila['Q'])} "
            f"{int(fila['R'])} "
            f"{int(fila['C'])} "
            f"{int(fila['H'])}"
        )

        resultados = (
            f"{int(fila['A'])} "
            f"{int(fila['E'])} "
            f"{int(fila['C1'])} "
            f"{int(fila['H1'])}"
        )

        print(f"{valores} | {resultados}")


if __name__ == "__main__":

    tabla = generar_tabla_verdad()
    resultados = contar_resultados(tabla)

    print("=== TABLA DE VERDAD LOGISMART ===")
    print()
    print(f"Combinaciones: {resultados['total']}")
    print(f"A = True: {resultados['A_true']}")
    print(f"E = True: {resultados['E_true']}")
    print(f"C1 = True: {resultados['C1_true']}")
    print(f"H1 = True: {resultados['H1_true']}")
    print()

    mostrar_tabla(tabla)

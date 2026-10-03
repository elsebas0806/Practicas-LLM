"""
Comparacion del clasificador por reglas de LogiSmart.
"""

import json

from llm.schemas import CorreoIncidente
from llm.classifier import IncidentClassifier


CATEGORIAS = [
    "soporte",
    "seguridad",
    "facturacion",
    "otro",
]


def cargar_correos():
    """Carga los 30 correos de evaluacion."""

    with open(
        "data/correos_evaluacion.json",
        "r",
        encoding="utf-8",
    ) as archivo:
        return json.load(archivo)


def clasificar_por_reglas(correo_data):
    """
    Utiliza directamente las reglas internas
    del clasificador.
    """

    correo = CorreoIncidente(
        remitente="evaluacion@test.com",
        asunto=correo_data["asunto"],
        cuerpo=correo_data["cuerpo"],
    )

    resultado = IncidentClassifier._clasificar_por_reglas(
        correo
    )

    return resultado.categoria


def construir_matriz(resultados):
    """Construye una matriz de confusion."""

    matriz = {
        esperada: {
            predicha: 0
            for predicha in CATEGORIAS
        }
        for esperada in CATEGORIAS
    }

    for resultado in resultados:

        esperada = resultado["esperada"]
        predicha = resultado["predicha"]

        if (
            esperada in matriz
            and predicha in matriz[esperada]
        ):
            matriz[esperada][predicha] += 1

    return matriz


def mostrar_matriz(matriz):
    """Muestra la matriz de confusion."""

    print("\n=== MATRIZ DE CONFUSION - REGLAS ===")

    encabezado = "Esperada".ljust(15)

    for categoria in CATEGORIAS:
        encabezado += categoria.ljust(15)

    print(encabezado)
    print("-" * len(encabezado))

    for esperada in CATEGORIAS:

        fila = esperada.ljust(15)

        for predicha in CATEGORIAS:
            fila += str(
                matriz[esperada][predicha]
            ).ljust(15)

        print(fila)


def main():
    """Ejecuta la evaluacion de reglas."""

    correos = cargar_correos()

    print("=== EVALUACION DEL CLASIFICADOR POR REGLAS ===")
    print(
        f"Correos disponibles: "
        f"{len(correos)}"
    )

    resultados = []

    for correo in correos:

        predicha = clasificar_por_reglas(
            correo
        )

        resultado = {
            "id": correo["id"],
            "esperada": correo[
                "categoria_esperada"
            ],
            "predicha": predicha,
        }

        resultados.append(resultado)

        print(
            f"ID {correo['id']}: "
            f"esperada={resultado['esperada']} | "
            f"predicha={resultado['predicha']}"
        )

    total = len(resultados)

    aciertos = sum(
        resultado["esperada"]
        == resultado["predicha"]
        for resultado in resultados
    )

    exactitud = (
        aciertos / total
        if total
        else 0
    )

    print("\n=== RESULTADOS ===")
    print(f"Total: {total}")
    print(f"Aciertos: {aciertos}")
    print(f"Errores: {total - aciertos}")
    print(f"Exactitud: {exactitud:.2%}")

    matriz = construir_matriz(
        resultados
    )

    mostrar_matriz(matriz)

    with open(
        "evaluacion_reglas.json",
        "w",
        encoding="utf-8",
    ) as archivo:

        json.dump(
            {
                "total": total,
                "aciertos": aciertos,
                "errores": total - aciertos,
                "exactitud": exactitud,
                "matriz_confusion": matriz,
                "resultados": resultados,
            },
            archivo,
            ensure_ascii=False,
            indent=4,
        )

    print(
        "\nResultados guardados en "
        "evaluacion_reglas.json"
    )


if __name__ == "__main__":
    main()
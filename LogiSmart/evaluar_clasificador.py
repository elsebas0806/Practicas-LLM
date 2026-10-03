"""
Comparacion de clasificadores de LogiSmart.

Evalua los mismos 30 correos mediante:
1. Reglas
2. LLM
3. Clasificador hibrido

Guarda los resultados para poder analizar
exactitud, errores, latencia y matriz de confusion.
"""

import json
import time

from llm.classifier import IncidentClassifier
from llm.schemas import CorreoIncidente


CATEGORIAS = [
    "soporte",
    "seguridad",
    "facturacion",
    "otro",
]


def cargar_correos():
    """Carga los correos etiquetados manualmente."""

    with open(
        "data/correos_evaluacion.json",
        "r",
        encoding="utf-8",
    ) as archivo:
        return json.load(archivo)


def crear_correo(correo_data):
    """Convierte un registro JSON en un objeto Pydantic."""

    return CorreoIncidente(
        remitente="evaluacion@test.com",
        asunto=correo_data["asunto"],
        cuerpo=correo_data["cuerpo"],
    )


def clasificar_reglas(clasificador, correo):
    """Clasifica utilizando solamente las reglas."""

    resultado = clasificador._clasificar_por_reglas(
        correo
    )

    return resultado


def clasificar_llm(clasificador, correo):
    """Clasifica utilizando solamente el LLM."""

    return clasificador._clasificar_por_llm(
        correo
    )


def clasificar_hibrido(clasificador, correo):
    """Clasifica utilizando LLM + reglas."""

    return clasificador.clasificar(
        correo
    )


def construir_matriz(resultados, campo_prediccion):
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
        predicha = resultado[campo_prediccion]

        if (
            esperada in matriz
            and predicha in matriz[esperada]
        ):
            matriz[esperada][predicha] += 1

    return matriz


def calcular_metricas(resultados, campo_prediccion):
    """Calcula exactitud y errores."""

    total = len(resultados)

    aciertos = sum(
        resultado["esperada"]
        == resultado[campo_prediccion]
        for resultado in resultados
    )

    errores = total - aciertos

    exactitud = (
        aciertos / total
        if total
        else 0
    )

    return {
        "total": total,
        "aciertos": aciertos,
        "errores": errores,
        "exactitud": exactitud,
    }


def mostrar_matriz(nombre, matriz):
    """Muestra una matriz de confusion."""

    print(
        f"\n=== MATRIZ DE CONFUSION - {nombre.upper()} ==="
    )

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
    """Ejecuta la comparacion completa."""

    correos = cargar_correos()

    print("=== COMPARACION DE CLASIFICADORES ===")
    print(
        f"Correos disponibles: "
        f"{len(correos)}"
    )

    print("\nSe evaluaran:")
    print("- Reglas")
    print("- LLM")
    print("- Hibrido")

    print(
        "\nATENCION: "
        "la evaluacion del LLM puede tardar varios minutos."
    )

    clasificador = IncidentClassifier()

    resultados = []

    for numero, correo_data in enumerate(
        correos,
        start=1,
    ):

        correo = crear_correo(
            correo_data
        )

        print(
            f"\n[{numero}/{len(correos)}] "
            f"Procesando ID {correo_data['id']}..."
        )

        # --------------------------------------------------
        # 1. REGLAS
        # --------------------------------------------------

        inicio_reglas = time.perf_counter()

        resultado_reglas = clasificar_reglas(
            clasificador,
            correo,
        )

        latencia_reglas = (
            time.perf_counter()
            - inicio_reglas
        ) * 1000

        # --------------------------------------------------
        # 2. LLM
        # --------------------------------------------------

        inicio_llm = time.perf_counter()

        resultado_llm = clasificar_llm(
            clasificador,
            correo,
        )

        latencia_llm = (
            time.perf_counter()
            - inicio_llm
        ) * 1000

        if resultado_llm is None:

            predicha_llm = "error"
            prioridad_llm = "error"

        else:

            predicha_llm = (
                resultado_llm.categoria
            )

            prioridad_llm = (
                resultado_llm.prioridad
            )

        # --------------------------------------------------
        # 3. HIBRIDO
        # --------------------------------------------------

        inicio_hibrido = time.perf_counter()

        resultado_hibrido = clasificar_hibrido(
            clasificador,
            correo,
        )

        latencia_hibrido = (
            time.perf_counter()
            - inicio_hibrido
        ) * 1000

        # --------------------------------------------------
        # RESULTADO
        # --------------------------------------------------

        resultado = {
            "id": correo_data["id"],
            "esperada": correo_data[
                "categoria_esperada"
            ],

            "reglas": resultado_reglas.categoria,

            "llm": predicha_llm,

            "hibrido": resultado_hibrido.categoria,

            "prioridad_esperada": correo_data[
                "prioridad_esperada"
            ],

            "prioridad_llm": prioridad_llm,

            "prioridad_hibrido": (
                resultado_hibrido.prioridad
            ),

            "revision_humana": (
                resultado_hibrido
                .requiere_revision_humana
            ),

            "latencia_reglas_ms": round(
                latencia_reglas,
                2,
            ),

            "latencia_llm_ms": round(
                latencia_llm,
                2,
            ),

            "latencia_hibrido_ms": round(
                latencia_hibrido,
                2,
            ),
        }

        resultados.append(resultado)

        print(
            f"    Esperada : "
            f"{resultado['esperada']}"
        )

        print(
            f"    Reglas   : "
            f"{resultado['reglas']}"
        )

        print(
            f"    LLM      : "
            f"{resultado['llm']}"
        )

        print(
            f"    Hibrido  : "
            f"{resultado['hibrido']}"
        )

    # ------------------------------------------------------
    # METRICAS
    # ------------------------------------------------------

    metricas_reglas = calcular_metricas(
        resultados,
        "reglas",
    )

    metricas_llm = calcular_metricas(
        resultados,
        "llm",
    )

    metricas_hibrido = calcular_metricas(
        resultados,
        "hibrido",
    )

    # ------------------------------------------------------
    # LATENCIAS
    # ------------------------------------------------------

    total = len(resultados)

    latencia_reglas_promedio = (
        sum(
            r["latencia_reglas_ms"]
            for r in resultados
        )
        / total
        if total
        else 0
    )

    latencia_llm_promedio = (
        sum(
            r["latencia_llm_ms"]
            for r in resultados
        )
        / total
        if total
        else 0
    )

    latencia_hibrido_promedio = (
        sum(
            r["latencia_hibrido_ms"]
            for r in resultados
        )
        / total
        if total
        else 0
    )

    revisiones = sum(
        r["revision_humana"]
        for r in resultados
    )

    # ------------------------------------------------------
    # MOSTRAR RESULTADOS
    # ------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("RESULTADOS FINALES")
    print("=" * 60)

    print("\nREGLAS")
    print(
        f"Exactitud: "
        f"{metricas_reglas['exactitud']:.2%}"
    )
    print(
        f"Aciertos: "
        f"{metricas_reglas['aciertos']}"
    )
    print(
        f"Errores: "
        f"{metricas_reglas['errores']}"
    )
    print(
        f"Latencia promedio: "
        f"{latencia_reglas_promedio:.2f} ms"
    )

    print("\nLLM")
    print(
        f"Exactitud: "
        f"{metricas_llm['exactitud']:.2%}"
    )
    print(
        f"Aciertos: "
        f"{metricas_llm['aciertos']}"
    )
    print(
        f"Errores: "
        f"{metricas_llm['errores']}"
    )
    print(
        f"Latencia promedio: "
        f"{latencia_llm_promedio:.2f} ms"
    )

    print("\nHIBRIDO")
    print(
        f"Exactitud: "
        f"{metricas_hibrido['exactitud']:.2%}"
    )
    print(
        f"Aciertos: "
        f"{metricas_hibrido['aciertos']}"
    )
    print(
        f"Errores: "
        f"{metricas_hibrido['errores']}"
    )
    print(
        f"Latencia promedio: "
        f"{latencia_hibrido_promedio:.2f} ms"
    )
    print(
        f"Revisiones humanas: "
        f"{revisiones}"
    )

    # ------------------------------------------------------
    # MATRICES
    # ------------------------------------------------------

    matriz_reglas = construir_matriz(
        resultados,
        "reglas",
    )

    matriz_llm = construir_matriz(
        resultados,
        "llm",
    )

    matriz_hibrido = construir_matriz(
        resultados,
        "hibrido",
    )

    mostrar_matriz(
        "reglas",
        matriz_reglas,
    )

    mostrar_matriz(
        "llm",
        matriz_llm,
    )

    mostrar_matriz(
        "hibrido",
        matriz_hibrido,
    )

    # ------------------------------------------------------
    # GUARDAR JSON
    # ------------------------------------------------------

    datos_finales = {
        "total": total,

        "reglas": {
            **metricas_reglas,
            "latencia_promedio_ms": (
                latencia_reglas_promedio
            ),
            "matriz_confusion": matriz_reglas,
        },

        "llm": {
            **metricas_llm,
            "latencia_promedio_ms": (
                latencia_llm_promedio
            ),
            "matriz_confusion": matriz_llm,
        },

        "hibrido": {
            **metricas_hibrido,
            "latencia_promedio_ms": (
                latencia_hibrido_promedio
            ),
            "revisiones_humanas": revisiones,
            "matriz_confusion": matriz_hibrido,
        },

        "resultados": resultados,
    }

    with open(
        "comparacion_clasificadores.json",
        "w",
        encoding="utf-8",
    ) as archivo:

        json.dump(
            datos_finales,
            archivo,
            ensure_ascii=False,
            indent=4,
        )

    print(
        "\nResultados guardados en "
        "comparacion_clasificadores.json"
    )


if __name__ == "__main__":
    main()
"""
Gestión de riesgos éticos de LogiSmart.
"""

from datetime import datetime, timezone

from database.repository import EthicalRiskRepository


RIESGOS_DEMO = [
    {
        "modulo": "LLM",
        "descripcion": (
            "El modelo puede generar una clasificación o explicación "
            "incorrecta."
        ),
        "categoria": "alucinaciones",
        "probabilidad": 3,
        "impacto": 5,
        "mitigacion": (
            "Validar respuestas con Pydantic, utilizar reglas "
            "deterministas y permitir revisión humana."
        ),
    },
    {
        "modulo": "Clasificador",
        "descripcion": (
            "El sistema puede clasificar de forma diferente "
            "correos escritos con errores o lenguaje informal."
        ),
        "categoria": "sesgo",
        "probabilidad": 3,
        "impacto": 4,
        "mitigacion": (
            "Evaluar ejemplos con distintas formas de escritura "
            "y revisar errores de clasificación."
        ),
    },
    {
        "modulo": "MongoDB",
        "descripcion": (
            "Los registros pueden contener información relacionada "
            "con operadores y conductores."
        ),
        "categoria": "privacidad",
        "probabilidad": 2,
        "impacto": 5,
        "mitigacion": (
            "Limitar los datos almacenados, controlar el acceso "
            "y evitar información personal innecesaria."
        ),
    },
    {
        "modulo": "Motor de decisiones",
        "descripcion": (
            "Los usuarios pueden depender demasiado de las decisiones "
            "automáticas del sistema."
        ),
        "categoria": "automatizacion",
        "probabilidad": 3,
        "impacto": 5,
        "mitigacion": (
            "Mantener revisión humana para casos ambiguos "
            "o de alto riesgo."
        ),
    },
]


def cargar_riesgos_demo() -> list[str]:
    """Carga riesgos éticos iniciales en MongoDB."""

    repositorio = EthicalRiskRepository()
    ids = []

    for riesgo in RIESGOS_DEMO:

        documento = {
            **riesgo,
            "historial": [
                {
                    "accion": "creacion",
                    "fecha": datetime.now(timezone.utc),
                    "usuario": "sistema",
                }
            ],
            "fecha_creacion": datetime.now(timezone.utc),
        }

        ids.append(
            repositorio.crear(documento)
        )

    return ids


if __name__ == "__main__":

    print("=== CARGANDO RIESGOS ETICOS ===")

    ids = cargar_riesgos_demo()

    print(f"Riesgos insertados: {len(ids)}")

    for riesgo_id in ids:
        print(f"- {riesgo_id}")
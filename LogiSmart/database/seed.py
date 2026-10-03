"""
Datos de demostración para LogiSmart.
"""

from database.repository import IncidentRepository


INCIDENTES_DEMO = [
    {
        "tipo": "soporte",
        "categoria": "soporte",
        "prioridad": "alta",
        "descripcion": "Cliente no puede acceder a su cuenta.",
        "requiere_escalamiento": False,
    },
    {
        "tipo": "seguridad",
        "categoria": "seguridad",
        "prioridad": "critica",
        "descripcion": "Cliente reporta actividad sospechosa en su cuenta.",
        "requiere_escalamiento": True,
    },
    {
        "tipo": "facturacion",
        "categoria": "facturacion",
        "prioridad": "media",
        "descripcion": "Cliente reporta un cobro incorrecto.",
        "requiere_escalamiento": False,
    },
    {
        "tipo": "otro",
        "categoria": "otro",
        "prioridad": "baja",
        "descripcion": "Consulta general sobre el servicio.",
        "requiere_escalamiento": False,
    },
]


def cargar_datos_demo() -> list[str]:
    """Inserta los incidentes de demostración."""
    repositorio = IncidentRepository()
    ids = []

    for incidente in INCIDENTES_DEMO:
        ids.append(repositorio.crear(incidente))

    return ids


if __name__ == "__main__":
    ids = cargar_datos_demo()

    print(f"Se insertaron {len(ids)} incidentes de demostración.")

    for incidente_id in ids:
        print(f"- {incidente_id}")

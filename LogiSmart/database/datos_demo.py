"""
Datos de demostración de LogiSmart.
"""

from datetime import datetime, timezone

from database.repository import TruckRepository, AccessRepository
from logic.reglas import evaluar_reglas, explicar_decision


CAMIONES_DEMO = [
    {
        "placa": "CAM-101",
        "camion_id": "CAM-101",
        "empresa": "Logistica Demo SA",
        "autorizacion": True,
        "certificacion_conductor": True,
    },
    {
        "placa": "CAM-102",
        "camion_id": "CAM-102",
        "empresa": "Transporte Seguro MX",
        "autorizacion": True,
        "certificacion_conductor": True,
    },
    {
        "placa": "CAM-103",
        "camion_id": "CAM-103",
        "empresa": "Carga Nacional",
        "autorizacion": False,
        "certificacion_conductor": False,
    },
]


ACCESOS_DEMO = [
    {
        "camion_id": "CAM-101",
        "operador": "operador_demo",
        "P": True,
        "Q": False,
        "R": False,
        "S": True,
        "C": True,
        "H": True,
    },
    {
        "camion_id": "CAM-102",
        "operador": "operador_demo",
        "P": True,
        "Q": True,
        "R": True,
        "S": True,
        "C": True,
        "H": True,
    },
    {
        "camion_id": "CAM-103",
        "operador": "operador_demo",
        "P": True,
        "Q": False,
        "R": False,
        "S": False,
        "C": False,
        "H": False,
    },
]


def cargar_camiones():
    repositorio = TruckRepository()
    ids = []

    for camion in CAMIONES_DEMO:
        ids.append(repositorio.crear(camion))

    return ids


def cargar_accesos():
    repositorio = AccessRepository()
    ids = []

    for acceso in ACCESOS_DEMO:

        resultados = evaluar_reglas(
            P=acceso["P"],
            S=acceso["S"],
            Q=acceso["Q"],
            R=acceso["R"],
            C=acceso["C"],
            H=acceso["H"],
        )

        documento = {
            "camion_id": acceso["camion_id"],
            "operador": acceso["operador"],
            "P": acceso["P"],
            "Q": acceso["Q"],
            "R": acceso["R"],
            "S": acceso["S"],
            "C": acceso["C"],
            "H": acceso["H"],
            "resultado_A": resultados["A"],
            "resultado_E": resultados["E"],
            "resultado_C1": resultados["C1"],
            "resultado_H1": resultados["H1"],
            "explicacion": explicar_decision(
                P=acceso["P"],
                S=acceso["S"],
                Q=acceso["Q"],
                R=acceso["R"],
                C=acceso["C"],
                H=acceso["H"],
            ),
            "fecha": datetime.now(timezone.utc),
        }

        ids.append(repositorio.crear(documento))

    return ids


if __name__ == "__main__":

    print("=== CARGANDO DATOS DE DEMOSTRACIÓN ===")

    camiones = cargar_camiones()
    print(f"Camiones insertados: {len(camiones)}")

    accesos = cargar_accesos()
    print(f"Accesos insertados: {len(accesos)}")

    print("Datos de demostración cargados correctamente.")

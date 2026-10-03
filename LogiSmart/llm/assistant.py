"""
Asistente explicativo de LogiSmart.

Implementa un RAG sencillo:
1. Busca información en MongoDB.
2. Construye contexto con registros reales.
3. Añade la explicación de las reglas lógicas.
4. Envía únicamente ese contexto al LLM.
5. Devuelve respuesta y fuentes.
"""

import json

from database.repository import (
    AccessRepository,
    IncidentRepository,
    TruckRepository,
)
from logic.reglas import explicar_decision
from llm.ollama_client import OllamaClient


SYSTEM_PROMPT = """
Eres el asistente explicativo de LogiSmart.

Tu función es explicar decisiones utilizando únicamente
los registros recuperados desde MongoDB.

REGLAS OBLIGATORIAS:

1. Utiliza únicamente la información incluida en el contexto.
2. No inventes datos.
3. No supongas información que no aparezca en el contexto.
4. Explica las decisiones lógicas paso a paso cuando existan.
5. Si el contexto no contiene información suficiente,
   responde exactamente:

"No tengo información suficiente en los registros de LogiSmart."

6. Cuando utilices un registro, menciona la fuente.
7. Responde en español.
8. Sé claro y breve.
"""


class LogiSmartAssistant:
    """Asistente RAG conectado a MongoDB y Ollama."""

    def __init__(
        self,
        cliente: OllamaClient | None = None,
    ):
        self.cliente = cliente or OllamaClient()

        self.repositorio_accesos = AccessRepository()
        self.repositorio_incidentes = IncidentRepository()
        self.repositorio_camiones = TruckRepository()

    def buscar_contexto(self, pregunta: str) -> dict:
        """Busca registros relevantes en MongoDB."""

        pregunta_minuscula = pregunta.lower()

        contexto = {
            "camiones": [],
            "accesos": [],
            "incidentes": [],
            "explicaciones_reglas": [],
        }

        # -------------------------------------------------
        # CAMIONES
        # -------------------------------------------------

        camiones = self.repositorio_camiones.listar(limite=100)

        for camion in camiones:
            placa = str(camion.get("placa", "")).lower()
            camion_id = str(camion.get("camion_id", "")).lower()

            if (
                placa
                and placa in pregunta_minuscula
            ) or (
                camion_id
                and camion_id in pregunta_minuscula
            ):
                contexto["camiones"].append(camion)

        # -------------------------------------------------
        # ACCESOS
        # -------------------------------------------------

        accesos = self.repositorio_accesos.listar(limite=100)

        for acceso in accesos:
            camion_id = str(
                acceso.get("camion_id", "")
            ).lower()

            if (
                camion_id
                and camion_id in pregunta_minuscula
            ):
                contexto["accesos"].append(acceso)

                P = bool(acceso.get("P", False))
                S = bool(acceso.get("S", False))
                Q = bool(acceso.get("Q", False))
                R = bool(acceso.get("R", False))
                C = bool(acceso.get("C", True))
                H = bool(acceso.get("H", True))

                explicacion = explicar_decision(
                    P=P,
                    S=S,
                    Q=Q,
                    R=R,
                    C=C,
                    H=H,
                )

                contexto["explicaciones_reglas"].append(
                    {
                        "camion_id": acceso.get("camion_id"),
                        "explicacion": explicacion,
                        "resultados": {
                            "A": acceso.get("A"),
                            "E": acceso.get("E"),
                            "C1": acceso.get("C1"),
                            "H1": acceso.get("H1"),
                        },
                    }
                )

        # -------------------------------------------------
        # INCIDENTES
        # -------------------------------------------------

        incidentes = self.repositorio_incidentes.listar(
            limite=100
        )

        palabras = [
            palabra
            for palabra in pregunta_minuscula.split()
            if len(palabra) > 3
        ]

        for incidente in incidentes:
            texto = json.dumps(
                incidente,
                ensure_ascii=False,
                default=str,
            ).lower()

            if any(
                palabra in texto
                for palabra in palabras
            ):
                contexto["incidentes"].append(incidente)

        return contexto

    @staticmethod
    def hay_contexto(contexto: dict) -> bool:
        """Indica si existe información recuperada."""

        return any(
            len(valor) > 0
            for valor in contexto.values()
        )

    def responder(self, pregunta: str) -> dict:
        """Responde una pregunta utilizando RAG."""

        contexto = self.buscar_contexto(pregunta)

        if not self.hay_contexto(contexto):
            return {
                "respuesta": (
                    "No tengo información suficiente "
                    "en los registros de LogiSmart."
                ),
                "fuentes": [],
                "contexto": contexto,
            }

        contexto_texto = json.dumps(
            contexto,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

        prompt = f"""
Pregunta del usuario:

{pregunta}

Información recuperada de MongoDB:

{contexto_texto}

Responde utilizando únicamente la información recuperada.

Si existen explicaciones_reglas, utilízalas para explicar
la decisión paso a paso.

Al final indica:

Fuente: MongoDB - registro correspondiente.
"""

        try:
            respuesta = self.cliente.generar(
                prompt=prompt,
                system=SYSTEM_PROMPT,
            )

        except Exception as exc:
            return {
                "respuesta": (
                    "No fue posible consultar el "
                    f"modelo local: {exc}"
                ),
                "fuentes": self._crear_fuentes(contexto),
                "contexto": contexto,
            }

        return {
            "respuesta": respuesta,
            "fuentes": self._crear_fuentes(contexto),
            "contexto": contexto,
        }

    @staticmethod
    def _crear_fuentes(contexto: dict) -> list[dict]:
        """Construye las fuentes utilizadas."""

        fuentes = []

        for camion in contexto["camiones"]:
            fuentes.append(
                {
                    "coleccion": "camiones",
                    "id": camion.get("_id"),
                }
            )

        for acceso in contexto["accesos"]:
            fuentes.append(
                {
                    "coleccion": "accesos",
                    "id": acceso.get("_id"),
                }
            )

        for incidente in contexto["incidentes"]:
            fuentes.append(
                {
                    "coleccion": "incidentes",
                    "id": incidente.get("_id"),
                }
            )

        return fuentes
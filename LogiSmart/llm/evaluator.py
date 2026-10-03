"""
Evaluación y registro de ejecuciones del LLM de LogiSmart.
"""

import time

from database.repository import LLMEvaluationRepository
from llm.ollama_client import OllamaClient


class LLMEvaluator:
    """Ejecuta una clasificación y registra métricas del LLM."""

    def __init__(
        self,
        cliente: OllamaClient | None = None,
        repositorio=None,
    ):
        self.cliente = cliente or OllamaClient()
        self.repositorio = (
            repositorio or LLMEvaluationRepository()
        )

    def ejecutar(
        self,
        prompt: str,
        system: str | None = None,
        clasificacion_reglas: str | None = None,
    ) -> dict:

        inicio = time.perf_counter()

        try:
            respuesta = self.cliente.generar(
                prompt=prompt,
                system=system,
            )

            error = None

        except Exception as exc:
            respuesta = ""
            error = str(exc)

        latencia_ms = (
            time.perf_counter() - inicio
        ) * 1000

        modelo = self.cliente.modelo

        coincide_reglas = None

        if clasificacion_reglas is not None:
            coincide_reglas = (
                respuesta.strip().lower()
                == clasificacion_reglas.strip().lower()
            )

        documento = {
            "prompt": prompt,
            "respuesta": respuesta,
            "modelo": modelo,
            "latencia_ms": round(latencia_ms, 2),
            "coincide_reglas": coincide_reglas,
            "error": error,
        }

        documento_id = self.repositorio.crear(
            documento
        )

        return {
            "id": documento_id,
            **documento,
        }
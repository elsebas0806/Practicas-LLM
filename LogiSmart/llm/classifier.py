"""
Clasificador híbrido de incidentes de LogiSmart.

Combina:
1. Clasificación mediante LLM local con Ollama.
2. Clasificación determinista mediante reglas.
3. Validación mediante Pydantic.
4. Reintento ante JSON inválido.
5. Fusión de resultados LLM + reglas.
6. Fallback a reglas si el LLM falla.
"""

import json

from llm.ollama_client import OllamaClient
from llm.schemas import ClasificacionIncidente, CorreoIncidente


SYSTEM_PROMPT = """
Eres el clasificador de incidentes de LogiSmart.

Debes devolver EXCLUSIVAMENTE un objeto JSON válido.

El JSON DEBE contener estos campos:

{
  "categoria": "soporte",
  "prioridad": "alta",
  "entidades": ["cuenta"],
  "resumen": "El cliente no puede acceder a su cuenta"
}

Categorias permitidas:
- soporte
- seguridad
- facturacion
- otro

Prioridades permitidas:
- baja
- media
- alta
- critica

Reglas:

- Problemas técnicos o de acceso -> soporte.
- Fraude, actividad sospechosa o riesgos de seguridad -> seguridad.
- Cobros, pagos o facturas -> facturacion.
- Si no corresponde a las anteriores -> otro.

Prioridades:

- Dudas generales -> baja.
- Problemas normales de facturación -> media.
- Pérdida de acceso a una cuenta -> alta.
- Seguridad, fraude o actividad sospechosa -> alta o critica.

entidades debe ser una lista de elementos relevantes.

resumen debe ser una explicación breve del problema.

No utilices Markdown.
No escribas texto antes o después del JSON.
"""


NIVELES_PRIORIDAD = {
    "baja": 1,
    "media": 2,
    "alta": 3,
    "critica": 4,
}


class IncidentClassifier:
    """Clasificador híbrido basado en LLM y reglas."""

    def __init__(
        self,
        cliente: OllamaClient | None = None,
    ):
        self.cliente = cliente or OllamaClient()

    def clasificar(
        self,
        correo: CorreoIncidente,
    ) -> ClasificacionIncidente:
        """
        Ejecuta una sola clasificación completa.

        La misma respuesta del LLM se utiliza para
        construir el resultado híbrido.
        """

        datos = self.clasificar_con_detalle(correo)

        return datos["hibrido"]

    def clasificar_con_detalle(
        self,
        correo: CorreoIncidente,
    ) -> dict:
        """
        Devuelve por separado:

        - resultado_llm
        - resultado_reglas
        - resultado_hibrido

        Esto evita ejecutar Ollama dos veces para
        el mismo correo.
        """

        resultado_llm = self._clasificar_por_llm(
            correo
        )

        resultado_reglas = self._clasificar_por_reglas(
            correo
        )

        if resultado_llm is None:

            print(
                "Aviso: el LLM no produjo una respuesta válida. "
                "Se utilizará el clasificador por reglas."
            )

            resultado_hibrido = resultado_reglas

        else:

            resultado_hibrido = self._fusionar_resultados(
                resultado_llm,
                resultado_reglas,
            )

        return {
            "llm": resultado_llm,
            "reglas": resultado_reglas,
            "hibrido": resultado_hibrido,
        }

    def _clasificar_por_llm(
        self,
        correo: CorreoIncidente,
    ) -> ClasificacionIncidente | None:

        for _ in range(2):

            try:

                prompt = self._crear_prompt(
                    correo
                )

                respuesta = self.cliente.generar(
                    prompt=prompt,
                    system=SYSTEM_PROMPT,
                )

                datos = self._extraer_json(
                    respuesta
                )

                resultado = (
                    ClasificacionIncidente.model_validate(
                        datos
                    )
                )

                return resultado

            except Exception:
                continue

        return None

    @staticmethod
    def _crear_prompt(
        correo: CorreoIncidente,
    ) -> str:

        return f"""
Analiza el siguiente correo.

Remitente:
{correo.remitente}

Asunto:
{correo.asunto}

Cuerpo:
{correo.cuerpo}

Devuelve solamente JSON válido con:
categoria, prioridad, entidades y resumen.
"""

    @staticmethod
    def _extraer_json(
        respuesta: str,
    ) -> dict:

        texto = respuesta.strip()

        if texto.startswith("```"):

            texto = texto.replace(
                "```json",
                "",
                1,
            )

            texto = texto.replace(
                "```",
                "",
            )

            texto = texto.strip()

        inicio = texto.find("{")
        fin = texto.rfind("}")

        if inicio == -1 or fin == -1 or fin <= inicio:

            raise ValueError(
                "Ollama no devolvió un JSON válido."
            )

        return json.loads(
            texto[inicio:fin + 1]
        )

    @staticmethod
    def _clasificar_por_reglas(
        correo: CorreoIncidente,
    ) -> ClasificacionIncidente:

        texto = (
            f"{correo.asunto} {correo.cuerpo}"
        ).lower()

        if any(
            palabra in texto
            for palabra in [
                "fraude",
                "sospechoso",
                "seguridad",
                "hack",
                "actividad extraña",
                "actividad sospechosa",
            ]
        ):

            categoria = "seguridad"
            prioridad = "critica"
            requiere = True

            motivo = (
                "El correo contiene indicadores "
                "relacionados con seguridad."
            )

        elif any(
            palabra in texto
            for palabra in [
                "cobro",
                "pago",
                "factura",
                "facturación",
                "facturacion",
            ]
        ):

            categoria = "facturacion"
            prioridad = "media"
            requiere = False

            motivo = (
                "El correo contiene información "
                "relacionada con facturación."
            )

        elif any(
            palabra in texto
            for palabra in [
                "cuenta",
                "acceso",
                "entrar",
                "error",
                "problema",
                "no funciona",
            ]
        ):

            categoria = "soporte"
            prioridad = "alta"
            requiere = False

            motivo = (
                "El correo contiene un problema "
                "técnico o de acceso."
            )

        else:

            categoria = "otro"
            prioridad = "baja"
            requiere = False

            motivo = (
                "No se identificó una categoría específica."
            )

        return ClasificacionIncidente(
            categoria=categoria,
            prioridad=prioridad,
            entidades=[],
            resumen=correo.cuerpo[:200],
            requiere_escalamiento=requiere,
            requiere_revision_humana=False,
            motivo=motivo,
            confianza=0.50,
        )

    @staticmethod
    def _fusionar_resultados(
        resultado_llm: ClasificacionIncidente,
        resultado_reglas: ClasificacionIncidente,
    ) -> ClasificacionIncidente:
        """
        Fusiona LLM y reglas.

        Si existe discrepancia se marca revisión humana.

        La prioridad de mayor nivel prevalece.
        """

        discrepancia_categoria = (
            resultado_llm.categoria
            != resultado_reglas.categoria
        )

        discrepancia_prioridad = (
            resultado_llm.prioridad
            != resultado_reglas.prioridad
        )

        hay_discrepancia = (
            discrepancia_categoria
            or discrepancia_prioridad
        )

        prioridad_llm = NIVELES_PRIORIDAD.get(
            resultado_llm.prioridad,
            0,
        )

        prioridad_reglas = NIVELES_PRIORIDAD.get(
            resultado_reglas.prioridad,
            0,
        )

        if prioridad_reglas > prioridad_llm:

            prioridad_final = (
                resultado_reglas.prioridad
            )

        else:

            prioridad_final = (
                resultado_llm.prioridad
            )

        if (
            resultado_llm.categoria
            == resultado_reglas.categoria
        ):

            categoria_final = (
                resultado_llm.categoria
            )

        elif (
            prioridad_reglas
            > prioridad_llm
        ):

            categoria_final = (
                resultado_reglas.categoria
            )

        else:

            categoria_final = (
                resultado_llm.categoria
            )

        requiere_escalamiento = (
            resultado_llm.requiere_escalamiento
            or resultado_reglas.requiere_escalamiento
        )

        motivo = resultado_llm.motivo

        if hay_discrepancia:

            motivo = (
                "Existe discrepancia entre LLM y reglas. "
                f"LLM={resultado_llm.categoria}/"
                f"{resultado_llm.prioridad}; "
                f"Reglas={resultado_reglas.categoria}/"
                f"{resultado_reglas.prioridad}."
            )

        return ClasificacionIncidente(
            categoria=categoria_final,
            prioridad=prioridad_final,
            entidades=resultado_llm.entidades,
            resumen=resultado_llm.resumen,
            requiere_escalamiento=requiere_escalamiento,
            requiere_revision_humana=hay_discrepancia,
            motivo=motivo,
            confianza=resultado_llm.confianza,
        )
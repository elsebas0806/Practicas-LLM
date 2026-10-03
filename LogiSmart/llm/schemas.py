"""
Esquemas de datos utilizados por el módulo LLM de LogiSmart.
"""

from pydantic import BaseModel, Field


class CorreoIncidente(BaseModel):
    """Representa un correo recibido por LogiSmart."""

    remitente: str
    asunto: str
    cuerpo: str


class ClasificacionIncidente(BaseModel):
    """
    Resultado final de la clasificación híbrida.

    Los cuatro campos principales provienen de la clasificación:
    categoria, prioridad, entidades y resumen.

    Los campos adicionales registran cómo se tomó la decisión.
    """

    categoria: str
    prioridad: str
    entidades: list[str]
    resumen: str

    requiere_escalamiento: bool = False
    requiere_revision_humana: bool = False
    motivo: str = ""
    confianza: float = Field(default=0.0, ge=0.0, le=1.0)
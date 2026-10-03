"""
Cliente para comunicarse con Ollama.
"""

import ollama


class OllamaClient:
    """Encapsula la comunicación con el servidor local de Ollama."""

    def __init__(self, modelo: str = "llama3.2"):
        self.modelo = modelo

    def verificar_conexion(self) -> bool:
        """Comprueba si Ollama está disponible y si el modelo existe."""
        try:
            respuesta = ollama.list()

            for modelo in respuesta.models:
                nombre = modelo.model

                if nombre == self.modelo or nombre.startswith(self.modelo + ":"):
                    return True

            return False

        except Exception:
            return False

    def generar(self, prompt: str, system: str | None = None) -> str:
        """Envía un prompt al modelo y devuelve su respuesta."""
        mensajes = []

        if system:
            mensajes.append({
                "role": "system",
                "content": system,
            })

        mensajes.append({
            "role": "user",
            "content": prompt,
        })

        respuesta = ollama.chat(
            model=self.modelo,
            messages=mensajes,
        )

        return respuesta["message"]["content"]

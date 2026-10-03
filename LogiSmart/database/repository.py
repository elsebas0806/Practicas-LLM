"""
Repositorios de persistencia de LogiSmart.

Cada repositorio trabaja con una colección específica de MongoDB.
"""

from datetime import datetime, timezone

from bson import ObjectId

from database.connection import MongoConnection


class BaseRepository:
    """Operaciones CRUD comunes para cualquier colección."""

    def __init__(self, collection_name: str, connection=None):
        self.connection = connection or MongoConnection()
        self.database = self.connection.connect()
        self.collection = self.database[collection_name]

    def crear(self, documento: dict) -> str:
        """Inserta un documento y devuelve su ID."""
        documento = dict(documento)

        if "fecha_creacion" not in documento:
            documento["fecha_creacion"] = datetime.now(timezone.utc)

        resultado = self.collection.insert_one(documento)
        return str(resultado.inserted_id)

    def obtener_por_id(self, documento_id: str) -> dict | None:
        """Obtiene un documento por su ID."""
        try:
            documento = self.collection.find_one(
                {"_id": ObjectId(documento_id)}
            )
        except Exception:
            return None

        if documento is None:
            return None

        documento["_id"] = str(documento["_id"])
        return documento

    def listar(self, limite: int = 50) -> list[dict]:
        """Devuelve los documentos más recientes."""
        documentos = (
            self.collection
            .find()
            .sort("fecha_creacion", -1)
            .limit(limite)
        )

        resultado = []

        for documento in documentos:
            documento["_id"] = str(documento["_id"])
            resultado.append(documento)

        return resultado

    def actualizar(self, documento_id: str, cambios: dict) -> bool:
        """Actualiza un documento."""
        try:
            resultado = self.collection.update_one(
                {"_id": ObjectId(documento_id)},
                {"$set": cambios},
            )
        except Exception:
            return False

        return resultado.modified_count > 0

    def eliminar(self, documento_id: str) -> bool:
        """Elimina un documento."""
        try:
            resultado = self.collection.delete_one(
                {"_id": ObjectId(documento_id)}
            )
        except Exception:
            return False

        return resultado.deleted_count > 0


class IncidentRepository(BaseRepository):
    """CRUD de la colección incidentes."""

    def __init__(self, connection=None):
        super().__init__("incidentes", connection)


class TruckRepository(BaseRepository):
    """CRUD de la colección camiones."""

    def __init__(self, connection=None):
        super().__init__("camiones", connection)


class AccessRepository(BaseRepository):
    """CRUD de la colección accesos."""

    def __init__(self, connection=None):
        super().__init__("accesos", connection)


class EthicalRiskRepository(BaseRepository):
    """CRUD de la colección riesgos_eticos."""

    def __init__(self, connection=None):
        super().__init__("riesgos_eticos", connection)


class LLMEvaluationRepository(BaseRepository):
    """CRUD de la colección evaluaciones_llm."""

    def __init__(self, connection=None):
        super().__init__("evaluaciones_llm", connection)


def agregar_incidentes_por_categoria_semana() -> list[dict]:
    """
    Agregación de incidentes por categoría y semana.
    """

    connection = MongoConnection()
    database = connection.connect()

    pipeline = [
    {
        "$match": {
            "clasificacion.categoria": {
                "$exists": True,
                "$ne": None,
            }
        }
    },
    {
        "$group": {
            "_id": {
                "categoria": "$clasificacion.categoria",
                "semana": {
                    "$isoWeek": "$fecha_creacion"
                },
                "anio": {
                    "$isoWeekYear": "$fecha_creacion"
                },
            },
            "cantidad": {
                "$sum": 1
            },
        }
    },
    {
        "$sort": {
            "_id.anio": 1,
            "_id.semana": 1,
            "_id.categoria": 1,
        }
    },
]

    documentos = database["incidentes"].aggregate(pipeline)

    return list(documentos)

class IncidentStatusRepository(IncidentRepository):
    """Operaciones específicas para el seguimiento de incidentes."""

    ESTADOS_VALIDOS = {
        "nuevo",
        "en_atencion",
        "cerrado",
    }

    def cambiar_estado(
        self,
        documento_id: str,
        nuevo_estado: str,
        operador: str = "sistema",
    ) -> bool:
        """
        Cambia el estado de un incidente y registra el historial.
        """

        if nuevo_estado not in self.ESTADOS_VALIDOS:
            raise ValueError(
                f"Estado inválido: {nuevo_estado}"
            )

        documento = self.obtener_por_id(documento_id)

        if documento is None:
            return False

        historial = documento.get("historial", [])

        historial.append(
            {
                "estado": nuevo_estado,
                "operador": operador,
                "fecha": datetime.now(timezone.utc),
            }
        )

        return self.actualizar(
            documento_id,
            {
                "estado": nuevo_estado,
                "historial": historial,
                "fecha_actualizacion": datetime.now(timezone.utc),
            },
        )
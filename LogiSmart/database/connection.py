"""
Conexión con MongoDB para LogiSmart.
"""

import os

from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()


class MongoConnection:
    """Gestiona la conexión con MongoDB."""

    def __init__(self):
        self.uri = os.getenv(
            "MONGODB_URI",
            "mongodb://localhost:27017",
        )
        self.database_name = os.getenv(
            "MONGODB_DATABASE",
            "logismart",
        )
        self.client = None

    def connect(self):
        """Crea y devuelve la conexión a MongoDB."""
        if self.client is None:
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=3000,
            )

        return self.client[self.database_name]

    def ping(self) -> bool:
        """Comprueba si MongoDB está disponible."""
        try:
            database = self.connect()
            database.command("ping")
            return True
        except Exception:
            return False

    def close(self):
        """Cierra la conexión."""
        if self.client is not None:
            self.client.close()
            self.client = None

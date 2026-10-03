"""
Configuración central de LogiSmart.
"""

import os

from dotenv import load_dotenv


load_dotenv()


APP_NAME = os.getenv(
    "APP_NAME",
    "LogiSmart",
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2",
)

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)

MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "logismart",
)

CONFIDENCE_MIN = float(
    os.getenv(
        "CONFIDENCE_MIN",
        "0.70",
    )
)

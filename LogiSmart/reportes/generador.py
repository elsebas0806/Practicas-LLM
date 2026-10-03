import csv
import json
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from database.repository import (
    TruckRepository,
    AccessRepository,
    IncidentRepository,
    EthicalRiskRepository,
)


class GeneradorReportes:
    def __init__(self):
        self.truck_repo = TruckRepository()
        self.access_repo = AccessRepository()
        self.incident_repo = IncidentRepository()
        self.risk_repo = EthicalRiskRepository()

        self.carpeta = Path("reportes_generados")
        self.carpeta.mkdir(exist_ok=True)

    def obtener_datos(self):
        return {
            "camiones": self.truck_repo.listar(1000),
            "accesos": self.access_repo.listar(1000),
            "incidentes": self.incident_repo.listar(1000),
            "riesgos_eticos": self.risk_repo.listar(1000),
        }

    def exportar_json(self):
        datos = self.obtener_datos()

        archivo = self.carpeta / "reporte_logismart.json"

        with open(
            archivo,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                datos,
                f,
                ensure_ascii=False,
                indent=4,
                default=str,
            )

        return str(archivo)

    def exportar_csv(self):
        datos = self.obtener_datos()

        archivos = []

        for nombre, registros in datos.items():

            archivo = self.carpeta / f"{nombre}.csv"

            if not registros:
                continue

            claves = set()

            for registro in registros:
                claves.update(
                    registro.keys()
                )

            claves = list(claves)

            with open(
                archivo,
                "w",
                newline="",
                encoding="utf-8",
            ) as f:

                writer = csv.DictWriter(
                    f,
                    fieldnames=claves,
                )

                writer.writeheader()

                for registro in registros:
                    fila = {}

                    for clave in claves:
                        valor = registro.get(
                            clave,
                            "",
                        )

                        if isinstance(
                            valor,
                            (dict, list),
                        ):
                            valor = json.dumps(
                                valor,
                                ensure_ascii=False,
                                default=str,
                            )

                        fila[clave] = valor

                    writer.writerow(fila)

            archivos.append(str(archivo))

        return archivos

    def exportar_pdf(self):
        datos = self.obtener_datos()

        archivo = self.carpeta / "reporte_logismart.pdf"

        pdf = canvas.Canvas(
            str(archivo),
            pagesize=letter,
        )

        ancho, alto = letter

        y = alto - 50

        pdf.setFont(
            "Helvetica-Bold",
            18,
        )

        pdf.drawString(
            50,
            y,
            "Reporte LogiSmart",
        )

        y -= 30

        pdf.setFont(
            "Helvetica",
            10,
        )

        resumen = [
            (
                "Camiones",
                len(datos["camiones"]),
            ),
            (
                "Accesos",
                len(datos["accesos"]),
            ),
            (
                "Incidentes",
                len(datos["incidentes"]),
            ),
            (
                "Riesgos éticos",
                len(datos["riesgos_eticos"]),
            ),
        ]

        for nombre, cantidad in resumen:

            pdf.drawString(
                60,
                y,
                f"{nombre}: {cantidad}",
            )

            y -= 20

        y -= 15

        pdf.setFont(
            "Helvetica-Bold",
            13,
        )

        pdf.drawString(
            50,
            y,
            "Incidentes",
        )

        y -= 25

        pdf.setFont(
            "Helvetica",
            9,
        )

        for incidente in datos["incidentes"]:

            clasificacion = incidente.get(
                "clasificacion",
                {},
            )

            categoria = clasificacion.get(
                "categoria",
                "sin categoria",
            )

            prioridad = clasificacion.get(
                "prioridad",
                "sin prioridad",
            )

            estado = incidente.get(
                "estado",
                "nuevo",
            )

            linea = (
                f"Categoria: {categoria} | "
                f"Prioridad: {prioridad} | "
                f"Estado: {estado}"
            )

            pdf.drawString(
                60,
                y,
                linea,
            )

            y -= 15

            if y < 50:
                pdf.showPage()

                y = alto - 50

                pdf.setFont(
                    "Helvetica",
                    9,
                )

        y -= 15

        pdf.setFont(
            "Helvetica-Bold",
            13,
        )

        pdf.drawString(
            50,
            y,
            "Riesgos eticos",
        )

        y -= 25

        pdf.setFont(
            "Helvetica",
            9,
        )

        for riesgo in datos["riesgos_eticos"]:

            modulo = riesgo.get(
                "modulo",
                "",
            )

            descripcion = riesgo.get(
                "descripcion",
                "",
            )

            probabilidad = riesgo.get(
                "probabilidad",
                0,
            )

            impacto = riesgo.get(
                "impacto",
                0,
            )

            puntuacion = (
                float(probabilidad)
                * float(impacto)
            )

            linea = (
                f"{modulo}: "
                f"riesgo={puntuacion}"
            )

            pdf.drawString(
                60,
                y,
                linea,
            )

            y -= 15

            if y < 50:
                pdf.showPage()

                y = alto - 50

                pdf.setFont(
                    "Helvetica",
                    9,
                )

        pdf.save()

        return str(archivo)
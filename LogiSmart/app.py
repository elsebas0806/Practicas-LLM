import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from itertools import product

from database.repository import (
    TruckRepository,
    AccessRepository,
    IncidentRepository,
    EthicalRiskRepository,
)
from logic.reglas import evaluar_reglas, explicar_decision
from llm.classifier import IncidentClassifier
from llm.schemas import CorreoIncidente
from llm.assistant import LogiSmartAssistant
from reportes.generador import GeneradorReportes
from database.connection import MongoConnection


# ============================================================
# CONFIGURACIÓN VISUAL
# ============================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


COLOR_FONDO = "#0B1120"
COLOR_SIDEBAR = "#111827"
COLOR_CARD = "#172033"
COLOR_CARD_2 = "#1E293B"
COLOR_PRIMARIO = "#3B82F6"
COLOR_PRIMARIO_HOVER = "#2563EB"
COLOR_VERDE = "#10B981"
COLOR_AMARILLO = "#F59E0B"
COLOR_ROJO = "#EF4444"
COLOR_TEXTO = "#F8FAFC"
COLOR_SECUNDARIO = "#94A3B8"
COLOR_BORDE = "#263449"


# ============================================================
# APP PRINCIPAL
# ============================================================

class LogiSmartApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("LogiSmart — Sistema Inteligente de Gestión")
        self.geometry("1450x900")
        self.minsize(1200, 750)
        self.configure(fg_color=COLOR_FONDO)

        self.truck_repo = TruckRepository()
        self.access_repo = AccessRepository()
        self.incident_repo = IncidentRepository()
        self.risk_repo = EthicalRiskRepository()

        self.classifier = IncidentClassifier()
        self.assistant = LogiSmartAssistant()
        self.reportes = GeneradorReportes()

        self.current_page = None
        self.pages = {}

        self.crear_interfaz()

        self.mostrar_pagina("Dashboard")

    # ========================================================
    # ESTRUCTURA GENERAL
    # ========================================================

    def crear_interfaz(self):

        self.sidebar = ctk.CTkFrame(
            self,
            width=245,
            corner_radius=0,
            fg_color=COLOR_SIDEBAR,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=COLOR_FONDO,
        )
        self.main.pack(side="right", fill="both", expand=True)

        self.crear_sidebar()

        self.content = ctk.CTkFrame(
            self.main,
            fg_color=COLOR_FONDO,
        )
        self.content.pack(fill="both", expand=True, padx=30, pady=25)

    # ========================================================
    # SIDEBAR
    # ========================================================

    def crear_sidebar(self):

        logo_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
        )
        logo_frame.pack(fill="x", padx=22, pady=(28, 35))

        logo = ctk.CTkLabel(
            logo_frame,
            text="LOGI",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLOR_PRIMARIO,
        )
        logo.pack(anchor="w")

        smart = ctk.CTkLabel(
            logo_frame,
            text="SMART",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLOR_TEXTO,
        )
        smart.pack(anchor="w")

        subtitulo = ctk.CTkLabel(
            logo_frame,
            text="Sistema inteligente",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_SECUNDARIO,
        )
        subtitulo.pack(anchor="w", pady=(4, 0))

        self.botones_sidebar = {}

        opciones = [
            ("Dashboard", "⌂"),
            ("Camiones", "▣"),
            ("Accesos", "✓"),
            ("Tabla de verdad", "◇"),
            ("Incidentes", "⚠"),
            ("Asistente LLM", "✦"),
            ("Riesgos éticos", "◈"),
            ("Reportes", "▤"),
            ("Configuración", "⚙"),
        ]

        for nombre, icono in opciones:

            boton = ctk.CTkButton(
                self.sidebar,
                text=f"  {icono}    {nombre}",
                height=46,
                corner_radius=10,
                anchor="w",
                fg_color="transparent",
                hover_color="#1E293B",
                text_color=COLOR_SECUNDARIO,
                font=ctk.CTkFont(size=14),
                command=lambda n=nombre: self.mostrar_pagina(n),
            )

            boton.pack(fill="x", padx=14, pady=3)

            self.botones_sidebar[nombre] = boton

        # Estado inferior

        estado = ctk.CTkFrame(
            self.sidebar,
            fg_color=COLOR_CARD,
            corner_radius=12,
        )
        estado.pack(side="bottom", fill="x", padx=15, pady=20)

        ctk.CTkLabel(
            estado,
            text="●  Sistema operativo",
            text_color=COLOR_VERDE,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(12, 2))

        ctk.CTkLabel(
            estado,
            text="MongoDB + Ollama",
            text_color=COLOR_SECUNDARIO,
            font=ctk.CTkFont(size=11),
        ).pack(anchor="w", padx=15, pady=(0, 12))

    # ========================================================
    # NAVEGACIÓN
    # ========================================================

    def limpiar_content(self):

        for widget in self.content.winfo_children():
            widget.destroy()

    def actualizar_sidebar(self, pagina):

        for nombre, boton in self.botones_sidebar.items():

            if nombre == pagina:
                boton.configure(
                    fg_color=COLOR_PRIMARIO,
                    text_color="white",
                )
            else:
                boton.configure(
                    fg_color="transparent",
                    text_color=COLOR_SECUNDARIO,
                )

    def mostrar_pagina(self, pagina):

        self.limpiar_content()
        self.actualizar_sidebar(pagina)

        self.current_page = pagina

        if pagina == "Dashboard":
            self.pagina_dashboard()

        elif pagina == "Camiones":
            self.pagina_camiones()

        elif pagina == "Accesos":
            self.pagina_accesos()

        elif pagina == "Tabla de verdad":
            self.pagina_verdad()

        elif pagina == "Incidentes":
            self.pagina_incidentes()

        elif pagina == "Asistente LLM":
            self.pagina_asistente()

        elif pagina == "Riesgos éticos":
            self.pagina_riesgos()

        elif pagina == "Reportes":
            self.pagina_reportes()

        elif pagina == "Configuración":
            self.pagina_configuracion()

    # ========================================================
    # ELEMENTOS REUTILIZABLES
    # ========================================================

    def titulo(self, titulo, descripcion=""):

        frame = ctk.CTkFrame(
            self.content,
            fg_color="transparent",
        )
        frame.pack(fill="x", pady=(0, 25))

        ctk.CTkLabel(
            frame,
            text=titulo,
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=COLOR_TEXTO,
        ).pack(anchor="w")

        if descripcion:

            ctk.CTkLabel(
                frame,
                text=descripcion,
                font=ctk.CTkFont(size=13),
                text_color=COLOR_SECUNDARIO,
            ).pack(anchor="w", pady=(5, 0))

    def tarjeta(self, parent, titulo, valor, descripcion, color):

        card = ctk.CTkFrame(
            parent,
            fg_color=COLOR_CARD,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_BORDE,
        )

        ctk.CTkLabel(
            card,
            text=titulo,
            font=ctk.CTkFont(size=13),
            text_color=COLOR_SECUNDARIO,
        ).pack(anchor="w", padx=20, pady=(18, 3))

        ctk.CTkLabel(
            card,
            text=str(valor),
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=color,
        ).pack(anchor="w", padx=20)

        ctk.CTkLabel(
            card,
            text=descripcion,
            font=ctk.CTkFont(size=11),
            text_color=COLOR_SECUNDARIO,
        ).pack(anchor="w", padx=20, pady=(3, 18))

        return card

    def crear_boton(self, parent, texto, comando, color=COLOR_PRIMARIO):

        return ctk.CTkButton(
            parent,
            text=texto,
            height=40,
            corner_radius=9,
            fg_color=color,
            hover_color=COLOR_PRIMARIO_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=comando,
        )

    # ========================================================
    # DASHBOARD
    # ========================================================

    def pagina_dashboard(self):

        self.titulo(
            "Dashboard",
            "Vista general del sistema LogiSmart",
        )

        try:
            camiones = self.truck_repo.listar(1000)
            accesos = self.access_repo.listar(1000)
            incidentes = self.incident_repo.listar(1000)
            riesgos = self.risk_repo.listar(1000)

            incidentes_abiertos = [
                x for x in incidentes
                if x.get("estado", "nuevo") != "cerrado"
            ]

            riesgos_criticos = [
                x for x in riesgos
                if float(x.get("probabilidad", 0))
                * float(x.get("impacto", 0)) >= 12
            ]

            mongo_ok = MongoConnection().ping()

        except Exception:
            camiones = []
            accesos = []
            incidentes_abiertos = []
            riesgos_criticos = []
            mongo_ok = False

        cards = ctk.CTkFrame(
            self.content,
            fg_color="transparent",
        )
        cards.pack(fill="x")

        for i in range(4):
            cards.grid_columnconfigure(i, weight=1)

        self.tarjeta(
            cards,
            "CAMIONES REGISTRADOS",
            len(camiones),
            "Vehículos en el sistema",
            COLOR_PRIMARIO,
        ).grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.tarjeta(
            cards,
            "ACCESOS EVALUADOS",
            len(accesos),
            "Decisiones registradas",
            COLOR_VERDE,
        ).grid(row=0, column=1, sticky="nsew", padx=8)

        self.tarjeta(
            cards,
            "INCIDENTES ABIERTOS",
            len(incidentes_abiertos),
            "Requieren seguimiento",
            COLOR_AMARILLO,
        ).grid(row=0, column=2, sticky="nsew", padx=8)

        self.tarjeta(
            cards,
            "RIESGOS CRÍTICOS",
            len(riesgos_criticos),
            "Requieren mitigación",
            COLOR_ROJO,
        ).grid(row=0, column=3, sticky="nsew", padx=(8, 0))

        # Estado del sistema

        estado_frame = ctk.CTkFrame(
            self.content,
            fg_color=COLOR_CARD,
            corner_radius=16,
        )
        estado_frame.pack(fill="x", pady=25)

        ctk.CTkLabel(
            estado_frame,
            text="Estado de infraestructura",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXTO,
        ).pack(anchor="w", padx=22, pady=(18, 12))

        servicios = [
            ("MongoDB", mongo_ok),
            ("Ollama", self.classifier.cliente.verificar_conexion()),
        ]

        for nombre, activo in servicios:

            fila = ctk.CTkFrame(
                estado_frame,
                fg_color="transparent",
            )
            fila.pack(fill="x", padx=22, pady=5)

            ctk.CTkLabel(
                fila,
                text=nombre,
                font=ctk.CTkFont(size=13),
                text_color=COLOR_TEXTO,
            ).pack(side="left")

            ctk.CTkLabel(
                fila,
                text="●  Conectado" if activo else "●  No disponible",
                text_color=COLOR_VERDE if activo else COLOR_ROJO,
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(side="right")

        ctk.CTkLabel(
            estado_frame,
            text="",
        ).pack(pady=5)

        # Acciones rápidas

        acciones = ctk.CTkFrame(
            self.content,
            fg_color="transparent",
        )
        acciones.pack(fill="x")

        ctk.CTkLabel(
            acciones,
            text="Acciones rápidas",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXTO,
        ).pack(anchor="w", pady=(0, 12))

        botones = ctk.CTkFrame(
            acciones,
            fg_color="transparent",
        )
        botones.pack(fill="x")

        self.crear_boton(
            botones,
            "+ Registrar camión",
            lambda: self.mostrar_pagina("Camiones"),
        ).pack(side="left", padx=(0, 10))

        self.crear_boton(
            botones,
            "✓ Evaluar acceso",
            lambda: self.mostrar_pagina("Accesos"),
        ).pack(side="left", padx=10)

        self.crear_boton(
            botones,
            "⚠ Ver incidentes",
            lambda: self.mostrar_pagina("Incidentes"),
        ).pack(side="left", padx=10)

        self.crear_boton(
            botones,
            "✦ Abrir asistente",
            lambda: self.mostrar_pagina("Asistente LLM"),
        ).pack(side="left", padx=10)

    # ========================================================
    # CAMIONES
    # ========================================================

    def pagina_camiones(self):

        self.titulo(
            "Gestión de camiones",
            "Alta, consulta y eliminación de vehículos autorizados",
        )

        formulario = ctk.CTkFrame(
            self.content,
            fg_color=COLOR_CARD,
            corner_radius=16,
        )
        formulario.pack(fill="x", pady=(0, 20))

        campos = ctk.CTkFrame(
            formulario,
            fg_color="transparent",
        )
        campos.pack(fill="x", padx=20, pady=20)

        self.camion_placa = self.crear_entry(
            campos,
            "Placa",
            0,
            0,
        )

        self.camion_id = self.crear_entry(
            campos,
            "ID del camión",
            0,
            1,
        )

        self.camion_empresa = self.crear_entry(
            campos,
            "Empresa",
            0,
            2,
        )

        self.camion_autorizacion = self.crear_entry(
            campos,
            "Autorización",
            0,
            3,
        )

        self.camion_certificacion = self.crear_entry(
            campos,
            "Certificación conductor",
            0,
            4,
        )

        self.crear_boton(
            formulario,
            "＋ Registrar camión",
            self.registrar_camion,
        ).pack(anchor="e", padx=20, pady=(0, 20))

        # Tabla

        tabla_frame = ctk.CTkFrame(
            self.content,
            fg_color=COLOR_CARD,
            corner_radius=16,
        )
        tabla_frame.pack(fill="both", expand=True)

        encabezado = ctk.CTkFrame(
            tabla_frame,
            fg_color="transparent",
        )
        encabezado.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            encabezado,
            text="Vehículos registrados",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXTO,
        ).pack(side="left")

        self.crear_boton(
            encabezado,
            "Actualizar",
            self.pagina_camiones,
        ).pack(side="right")

        self.camiones_scroll = ctk.CTkScrollableFrame(
            tabla_frame,
            fg_color="transparent",
        )
        self.camiones_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.cargar_camiones()

    def crear_entry(self, parent, placeholder, row, column):

        frame = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )

        frame.grid(
            row=row,
            column=column,
            sticky="ew",
            padx=5,
        )

        parent.grid_columnconfigure(column, weight=1)

        ctk.CTkLabel(
            frame,
            text=placeholder,
            text_color=COLOR_SECUNDARIO,
            font=ctk.CTkFont(size=11),
        ).pack(anchor="w", pady=(0, 5))

        entry = ctk.CTkEntry(
            frame,
            height=38,
            placeholder_text=placeholder,
            corner_radius=8,
        )
        entry.pack(fill="x")

        return entry

    def cargar_camiones(self):

        for widget in self.camiones_scroll.winfo_children():
            widget.destroy()

        camiones = self.truck_repo.listar(1000)

        encabezados = [
            "PLACA",
            "CAMIÓN",
            "EMPRESA",
            "AUTORIZACIÓN",
            "CERTIFICACIÓN",
            "ACCIÓN",
        ]

        for i, texto in enumerate(encabezados):

            ctk.CTkLabel(
                self.camiones_scroll,
                text=texto,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=COLOR_SECUNDARIO,
            ).grid(
                row=0,
                column=i,
                sticky="w",
                padx=10,
                pady=10,
            )

        for fila, camion in enumerate(camiones, start=1):

            datos = [
                camion.get("placa", ""),
                camion.get("camion_id", ""),
                camion.get("empresa", ""),
                str(camion.get("autorizacion", "")),
                str(camion.get("certificacion_conductor", "")),
            ]

            for col, dato in enumerate(datos):

                ctk.CTkLabel(
                    self.camiones_scroll,
                    text=str(dato),
                    text_color=COLOR_TEXTO,
                ).grid(
                    row=fila,
                    column=col,
                    sticky="w",
                    padx=10,
                    pady=8,
                )

            self.crear_boton(
                self.camiones_scroll,
                "Eliminar",
                lambda id=camion.get("_id"): self.eliminar_camion(id),
                COLOR_ROJO,
            ).grid(
                row=fila,
                column=5,
                padx=10,
                pady=5,
            )

    def registrar_camion(self):

        placa = self.camion_placa.get().strip()
        camion_id = self.camion_id.get().strip()
        empresa = self.camion_empresa.get().strip()

        if not placa or not camion_id or not empresa:
            messagebox.showwarning(
                "Datos incompletos",
                "Placa, ID del camión y empresa son obligatorios.",
            )
            return

        documento = {
            "placa": placa,
            "camion_id": camion_id,
            "empresa": empresa,
            "autorizacion": self.camion_autorizacion.get().strip(),
            "certificacion_conductor": self.camion_certificacion.get().strip(),
        }

        try:

            self.truck_repo.crear(documento)

            messagebox.showinfo(
                "Camión registrado",
                "El camión fue registrado correctamente.",
            )

            self.mostrar_pagina("Camiones")

        except Exception as exc:

            messagebox.showerror(
                "Error",
                f"No fue posible registrar el camión:\n{exc}",
            )

    def eliminar_camion(self, documento_id):

        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            "¿Deseas eliminar este camión?",
        )

        if not confirmar:
            return

        if self.truck_repo.eliminar(documento_id):

            self.mostrar_pagina("Camiones")

        else:

            messagebox.showerror(
                "Error",
                "No fue posible eliminar el camión.",
            )

    # ========================================================
    # ACCESOS
    # ========================================================

    def pagina_accesos(self):

        self.titulo(
            "Evaluación de acceso",
            "Motor lógico A, E, C1 y H1",
        )

        panel = ctk.CTkFrame(
            self.content,
            fg_color=COLOR_CARD,
            corner_radius=16,
        )
        panel.pack(fill="x")

        izquierda = ctk.CTkFrame(
            panel,
            fg_color="transparent",
        )
        izquierda.pack(side="left", fill="both", expand=True, padx=25, pady=25)

        derecha = ctk.CTkFrame(
            panel,
            fg_color=COLOR_CARD_2,
            corner_radius=12,
        )
        derecha.pack(side="right", fill="both", expand=True, padx=25, pady=25)

        ctk.CTkLabel(
            izquierda,
            text="Parámetros de evaluación",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", pady=(0, 20))

        self.acceso_camion = ctk.CTkEntry(
            izquierda,
            placeholder_text="ID del camión",
            height=40,
        )
        self.acceso_camion.pack(fill="x", pady=5)

        self.vars = {}

        opciones = [
            ("P", "Problema reportado"),
            ("S", "Evidencia suficiente"),
            ("Q", "Riesgo de seguridad"),
            ("R", "Riesgo reputacional"),
            ("C", "Certificación vigente"),
            ("H", "Horario permitido"),
        ]

        for clave, descripcion in opciones:

            var = ctk.BooleanVar(value=True)
            self.vars[clave] = var

            check = ctk.CTkCheckBox(
                izquierda,
                text=f"{clave} — {descripcion}",
                variable=var,
                font=ctk.CTkFont(size=13),
            )
            check.pack(anchor="w", pady=7)

        self.crear_boton(
            izquierda,
            "Evaluar decisión",
            self.evaluar_acceso,
        ).pack(fill="x", pady=(20, 0))

        ctk.CTkLabel(
            derecha,
            text="Resultado",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.acceso_resultado = ctk.CTkLabel(
            derecha,
            text="Esperando evaluación",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=COLOR_SECUNDARIO,
        )
        self.acceso_resultado.pack(padx=20, pady=15)

        self.acceso_explicacion = ctk.CTkTextbox(
            derecha,
            height=230,
            corner_radius=10,
        )
        self.acceso_explicacion.pack(fill="both", expand=True, padx=20, pady=(5, 20))

    def evaluar_acceso(self):

        P = self.vars["P"].get()
        S = self.vars["S"].get()
        Q = self.vars["Q"].get()
        R = self.vars["R"].get()
        C = self.vars["C"].get()
        H = self.vars["H"].get()

        resultado = evaluar_reglas(P, S, Q, R, C, H)

        if resultado["E"]:
            texto = "ENVIAR A INSPECCIÓN"
            color = COLOR_ROJO
        elif resultado["A"]:
            texto = "ACCESO APROBADO"
            color = COLOR_VERDE
        else:
            texto = "REVISIÓN REQUERIDA"
            color = COLOR_AMARILLO

        self.acceso_resultado.configure(
            text=texto,
            text_color=color,
        )

        self.acceso_explicacion.delete("1.0", "end")

        for linea in explicar_decision(
            P, S, Q, R, C, H
        ):
            self.acceso_explicacion.insert(
                "end",
                linea + "\n\n",
            )

        camion_id = self.acceso_camion.get().strip()

        documento = {
            "camion_id": camion_id,
            "P": P,
            "S": S,
            "Q": Q,
            "R": R,
            "C": C,
            "H": H,
            **resultado,
            "operador": "GUI",
            "timestamp": datetime.now().isoformat(),
            "explicacion": explicar_decision(
                P, S, Q, R, C, H
            ),
        }

        try:
            self.access_repo.crear(documento)

        except Exception as exc:

            messagebox.showwarning(
                "Evaluación",
                f"La evaluación fue realizada, pero no se pudo guardar:\n{exc}",
            )

    # ========================================================
    # TABLA DE VERDAD
    # ========================================================

    def pagina_verdad(self):

        self.titulo(
            "Tabla de verdad",
            "Simulador de reglas y tabla completa de las 64 combinaciones",
        )

        # ====================================================
        # SIMULADOR ACTUAL
        # ====================================================

        panel = ctk.CTkFrame(
            self.content,
            fg_color=COLOR_CARD,
            corner_radius=16,
        )
        panel.pack(fill="x", pady=(0, 15))

        self.truth_vars = {}

        variables = [
            ("P", "Problema"),
            ("S", "Evidencia"),
            ("Q", "Seguridad"),
            ("R", "Reputación"),
            ("C", "Certificación"),
            ("H", "Horario"),
        ]

        for i, (clave, nombre) in enumerate(variables):

            var = ctk.BooleanVar(value=True)
            self.truth_vars[clave] = var

            check = ctk.CTkCheckBox(
                panel,
                text=f"{clave} — {nombre}",
                variable=var,
                command=self.actualizar_truth,
            )
            check.grid(
                row=0,
                column=i,
                padx=12,
                pady=20,
            )

        # ====================================================
        # RESULTADOS ACTUALES
        # ====================================================

        resultados = ctk.CTkFrame(
            self.content,
            fg_color="transparent",
        )
        resultados.pack(fill="x", pady=(0, 15))

        self.truth_labels = {}

        for i, nombre in enumerate(
            [
                "A — Aprobar",
                "E — Escalar",
                "C1 — Certificación",
                "H1 — Horario",
            ]
        ):

            frame = ctk.CTkFrame(
                resultados,
                fg_color=COLOR_CARD,
                corner_radius=12,
            )
            frame.grid(
                row=0,
                column=i,
                sticky="nsew",
                padx=6,
            )

            resultados.grid_columnconfigure(i, weight=1)

            ctk.CTkLabel(
                frame,
                text=nombre,
                font=ctk.CTkFont(size=13),
                text_color=COLOR_SECUNDARIO,
            ).pack(pady=(12, 3))

            label = ctk.CTkLabel(
                frame,
                text="FALSE",
                font=ctk.CTkFont(size=22, weight="bold"),
            )
            label.pack(pady=(0, 12))

            self.truth_labels[nombre] = label

        self.actualizar_truth()

        # ====================================================
        # TABLA COMPLETA
        # ====================================================

        titulo_tabla = ctk.CTkFrame(
            self.content,
            fg_color="transparent",
        )
        titulo_tabla.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            titulo_tabla,
            text="Tabla completa",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLOR_TEXTO,
        ).pack(side="left")

        ctk.CTkLabel(
            titulo_tabla,
            text="64 combinaciones posibles",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_SECUNDARIO,
        ).pack(side="right")

        tabla_contenedor = ctk.CTkFrame(
            self.content,
            fg_color=COLOR_CARD,
            corner_radius=16,
        )
        tabla_contenedor.pack(
            fill="both",
            expand=True,
        )

        # Encabezados de la tabla

        encabezado = ctk.CTkFrame(
            tabla_contenedor,
            fg_color=COLOR_CARD_2,
            corner_radius=10,
        )
        encabezado.pack(
            fill="x",
            padx=12,
            pady=(12, 0),
        )

        encabezados = [
            "P",
            "S",
            "Q",
            "R",
            "C",
            "H",
            "A",
            "E",
            "C1",
            "H1",
        ]

        for columna, nombre in enumerate(encabezados):

            encabezado.grid_columnconfigure(
                columna,
                weight=1,
            )

            ctk.CTkLabel(
                encabezado,
                text=nombre,
                font=ctk.CTkFont(
                    size=12,
                    weight="bold",
                ),
                text_color=COLOR_TEXTO,
            ).grid(
                row=0,
                column=columna,
                sticky="nsew",
                padx=4,
                pady=10,
            )

        # Área con scroll

        tabla_scroll = ctk.CTkScrollableFrame(
            tabla_contenedor,
            fg_color="transparent",
        )
        tabla_scroll.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=10,
        )

        for columna in range(10):

            tabla_scroll.grid_columnconfigure(
                columna,
                weight=1,
            )

        # ====================================================
        # GENERACIÓN DE LAS 64 COMBINACIONES
        # ====================================================

        combinaciones = product(
            [False, True],
            repeat=6,
        )

        for fila, combinacion in enumerate(
            combinaciones,
            start=1,
        ):

            P, S, Q, R, C, H = combinacion

            resultado = evaluar_reglas(
                P,
                S,
                Q,
                R,
                C,
                H,
            )

            datos = [
                P,
                S,
                Q,
                R,
                C,
                H,
                resultado["A"],
                resultado["E"],
                resultado["C1"],
                resultado["H1"],
            ]

            # Separador visual cada fila

            fila_frame = ctk.CTkFrame(
                tabla_scroll,
                fg_color=(
                    COLOR_CARD
                    if fila % 2 == 1
                    else COLOR_CARD_2
                ),
                corner_radius=6,
            )
            fila_frame.grid(
                row=fila - 1,
                column=0,
                columnspan=10,
                sticky="ew",
                pady=1,
            )

            for columna, valor in enumerate(datos):

                texto = "1" if valor else "0"

                # Color especial para resultados
                if columna >= 6:
                    texto_color = (
                        COLOR_VERDE
                        if valor
                        else COLOR_ROJO
                    )
                else:
                    texto_color = COLOR_TEXTO

                ctk.CTkLabel(
                    fila_frame,
                    text=texto,
                    font=ctk.CTkFont(
                        size=12,
                        weight="bold" if columna >= 6 else "normal",
                    ),
                    text_color=texto_color,
                ).grid(
                    row=0,
                    column=columna,
                    sticky="nsew",
                    padx=4,
                    pady=5,
                )

                fila_frame.grid_columnconfigure(
                    columna,
                    weight=1,
                )

    def actualizar_truth(self):

        valores = {
            clave: var.get()
            for clave, var in self.truth_vars.items()
        }

        resultado = evaluar_reglas(
            valores["P"],
            valores["S"],
            valores["Q"],
            valores["R"],
            valores["C"],
            valores["H"],
        )

        claves = [
            ("A — Aprobar", "A"),
            ("E — Escalar", "E"),
            ("C1 — Certificación", "C1"),
            ("H1 — Horario", "H1"),
        ]

        for nombre, clave in claves:

            valor = resultado[clave]

            self.truth_labels[nombre].configure(
                text="TRUE" if valor else "FALSE",
                text_color=COLOR_VERDE if valor else COLOR_ROJO,
            )

    # ========================================================
    # INCIDENTES
    # ========================================================

    def pagina_incidentes(self):

        self.titulo(
            "Centro de incidentes",
            "Clasificación híbrida mediante reglas + Ollama",
        )

        formulario = ctk.CTkFrame(
            self.content,
            fg_color=COLOR_CARD,
            corner_radius=16,
        )
        formulario.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            formulario,
            text="Nuevo incidente",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.incidente_remitente = ctk.CTkEntry(
            formulario,
            placeholder_text="Remitente",
            height=40,
        )
        self.incidente_remitente.pack(fill="x", padx=20, pady=5)

        self.incidente_asunto = ctk.CTkEntry(
            formulario,
            placeholder_text="Asunto",
            height=40,
        )
        self.incidente_asunto.pack(fill="x", padx=20, pady=5)

        self.incidente_cuerpo = ctk.CTkTextbox(
            formulario,
            height=130,
        )
        self.incidente_cuerpo.pack(fill="x", padx=20, pady=5)

        self.crear_boton(
            formulario,
            "✦ Clasificar incidente",
            self.clasificar_incidente,
        ).pack(anchor="e", padx=20, pady=20)

        self.incidente_resultado = ctk.CTkTextbox(
            self.content,
            height=250,
            corner_radius=12,
        )
        self.incidente_resultado.pack(fill="x")

        ctk.CTkLabel(
            self.content,
            text="Incidentes registrados",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", pady=(20, 10))

        self.incidentes_lista = ctk.CTkScrollableFrame(
            self.content,
            fg_color=COLOR_CARD,
            corner_radius=12,
        )
        self.incidentes_lista.pack(fill="both", expand=True)

        self.cargar_incidentes()

    def clasificar_incidente(self):

        correo = CorreoIncidente(
            remitente=self.incidente_remitente.get().strip(),
            asunto=self.incidente_asunto.get().strip(),
            cuerpo=self.incidente_cuerpo.get("1.0", "end").strip(),
        )

        if not correo.asunto or not correo.cuerpo:

            messagebox.showwarning(
                "Datos incompletos",
                "Escribe el asunto y el cuerpo del correo.",
            )
            return

        self.incidente_resultado.delete("1.0", "end")
        self.incidente_resultado.insert(
            "end",
            "Clasificando con Ollama...\n\n",
        )

        self.update()

        try:

            resultados = self.classifier.clasificar_con_detalle(
                correo
            )

            hibrido = resultados["hibrido"]

            texto = (
                f"CATEGORÍA: {hibrido.categoria}\n"
                f"PRIORIDAD: {hibrido.prioridad}\n"
                f"ENTIDADES: {', '.join(hibrido.entidades)}\n\n"
                f"RESUMEN:\n{hibrido.resumen}\n\n"
                f"ESCALAMIENTO: {hibrido.requiere_escalamiento}\n"
                f"REVISIÓN HUMANA: {hibrido.requiere_revision_humana}\n\n"
                f"MOTIVO:\n{hibrido.motivo}\n\n"
                f"CONFIANZA: {hibrido.confianza:.2f}"
            )

            self.incidente_resultado.delete("1.0", "end")
            self.incidente_resultado.insert("end", texto)

            documento = {
                "correo": correo.model_dump(),
                "clasificacion": hibrido.model_dump(),
                "estado": "nuevo",
                "fecha": datetime.now().isoformat(),
                "historial": [
                    {
                        "estado": "nuevo",
                        "operador": "GUI",
                        "fecha": datetime.now().isoformat(),
                    }
                ],
            }

            self.incident_repo.crear(documento)

            self.cargar_incidentes()

        except Exception as exc:

            self.incidente_resultado.delete("1.0", "end")
            self.incidente_resultado.insert(
                "end",
                f"Error durante la clasificación:\n{exc}",
            )

    def cargar_incidentes(self):

        for widget in self.incidentes_lista.winfo_children():
            widget.destroy()

        incidentes = self.incident_repo.listar(100)

        if not incidentes:

            ctk.CTkLabel(
                self.incidentes_lista,
                text="No hay incidentes registrados.",
                text_color=COLOR_SECUNDARIO,
            ).pack(pady=30)

            return

        for incidente in incidentes:

            clasificacion = incidente.get(
                "clasificacion",
                {},
            )

            categoria = clasificacion.get(
                "categoria",
                "sin categoría",
            )

            prioridad = clasificacion.get(
                "prioridad",
                "sin prioridad",
            )

            estado = incidente.get(
                "estado",
                "nuevo",
            )

            frame = ctk.CTkFrame(
                self.incidentes_lista,
                fg_color=COLOR_CARD_2,
                corner_radius=10,
            )
            frame.pack(fill="x", padx=10, pady=6)

            ctk.CTkLabel(
                frame,
                text=categoria.upper(),
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(side="left", padx=15, pady=15)

            ctk.CTkLabel(
                frame,
                text=f"Prioridad: {prioridad}",
                text_color=COLOR_AMARILLO,
            ).pack(side="left", padx=15)

            ctk.CTkLabel(
                frame,
                text=f"Estado: {estado}",
                text_color=COLOR_SECUNDARIO,
            ).pack(side="right", padx=15)

    # ========================================================
    # ASISTENTE LLM
    # ========================================================

    def pagina_asistente(self):

        self.titulo(
            "Asistente inteligente",
            "Consulta información registrada en MongoDB mediante RAG",
        )

        chat = ctk.CTkFrame(
            self.content,
            fg_color=COLOR_CARD,
            corner_radius=16,
        )
        chat.pack(fill="both", expand=True)

        self.chat_historial = ctk.CTkTextbox(
            chat,
            corner_radius=12,
            font=ctk.CTkFont(size=13),
        )
        self.chat_historial.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20,
        )

        entrada = ctk.CTkFrame(
            chat,
            fg_color="transparent",
        )
        entrada.pack(fill="x", padx=20, pady=(0, 20))

        self.chat_pregunta = ctk.CTkEntry(
            entrada,
            placeholder_text="Ejemplo: ¿Por qué CAM-102 fue enviado a inspección?",
            height=45,
        )
        self.chat_pregunta.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 10),
        )

        self.crear_boton(
            entrada,
            "Enviar",
            self.enviar_pregunta,
        ).pack(side="right")

    def enviar_pregunta(self):

        pregunta = self.chat_pregunta.get().strip()

        if not pregunta:
            return

        self.chat_historial.insert(
            "end",
            f"\nTÚ\n{pregunta}\n\n",
        )

        self.chat_pregunta.delete(0, "end")

        self.update()

        try:

            resultado = self.assistant.responder(
                pregunta
            )

            respuesta = resultado["respuesta"]
            fuentes = resultado["fuentes"]

            self.chat_historial.insert(
                "end",
                f"LOGISMART\n{respuesta}\n\n",
            )

            if fuentes:

                self.chat_historial.insert(
                    "end",
                    "FUENTES:\n",
                )

                for fuente in fuentes:

                    self.chat_historial.insert(
                        "end",
                        f"- {fuente['coleccion']} / {fuente['id']}\n",
                    )

                self.chat_historial.insert(
                    "end",
                    "\n",
                )

        except Exception as exc:

            self.chat_historial.insert(
                "end",
                f"ERROR\n{exc}\n\n",
            )

    # ========================================================
    # RIESGOS ÉTICOS
    # ========================================================

    def pagina_riesgos(self):

        self.titulo(
            "Riesgos éticos",
            "Matriz de riesgos del sistema de inteligencia artificial",
        )

        riesgos = self.risk_repo.listar(100)

        contenedor = ctk.CTkScrollableFrame(
            self.content,
            fg_color="transparent",
        )
        contenedor.pack(fill="both", expand=True)

        for riesgo in riesgos:

            probabilidad = float(
                riesgo.get("probabilidad", 0)
            )

            impacto = float(
                riesgo.get("impacto", 0)
            )

            puntuacion = probabilidad * impacto

            if puntuacion >= 15:
                color = COLOR_ROJO
                nivel = "CRÍTICO"
            elif puntuacion >= 8:
                color = COLOR_AMARILLO
                nivel = "MEDIO"
            else:
                color = COLOR_VERDE
                nivel = "BAJO"

            card = ctk.CTkFrame(
                contenedor,
                fg_color=COLOR_CARD,
                corner_radius=14,
                border_width=1,
                border_color=COLOR_BORDE,
            )
            card.pack(fill="x", padx=5, pady=7)

            superior = ctk.CTkFrame(
                card,
                fg_color="transparent",
            )
            superior.pack(fill="x", padx=20, pady=(15, 5))

            ctk.CTkLabel(
                superior,
                text=riesgo.get("modulo", "Sin módulo"),
                font=ctk.CTkFont(size=17, weight="bold"),
            ).pack(side="left")

            ctk.CTkLabel(
                superior,
                text=f"{nivel}  •  {puntuacion:.0f}/25",
                text_color=color,
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(side="right")

            ctk.CTkLabel(
                card,
                text=riesgo.get("descripcion", ""),
                justify="left",
                wraplength=900,
                text_color=COLOR_SECUNDARIO,
            ).pack(anchor="w", padx=20, pady=5)

            ctk.CTkLabel(
                card,
                text=f"Categoría: {riesgo.get('categoria', '')}",
                text_color=COLOR_SECUNDARIO,
            ).pack(anchor="w", padx=20)

            ctk.CTkLabel(
                card,
                text=f"Mitigación: {riesgo.get('mitigacion', '')}",
                justify="left",
                wraplength=900,
                text_color=COLOR_TEXTO,
            ).pack(anchor="w", padx=20, pady=(5, 15))

    # ========================================================
    # REPORTES
    # ========================================================

    def pagina_reportes(self):

        self.titulo(
            "Centro de reportes",
            "Generación de reportes PDF, CSV y JSON",
        )

        panel = ctk.CTkFrame(
            self.content,
            fg_color=COLOR_CARD,
            corner_radius=16,
        )
        panel.pack(fill="x")

        opciones = [
            (
                "PDF",
                "Reporte ejecutivo completo",
                self.generar_pdf,
            ),
            (
                "CSV",
                "Datos tabulares para análisis",
                self.generar_csv,
            ),
            (
                "JSON",
                "Datos completos estructurados",
                self.generar_json,
            ),
        ]

        for titulo, descripcion, comando in opciones:

            fila = ctk.CTkFrame(
                panel,
                fg_color=COLOR_CARD_2,
                corner_radius=10,
            )
            fila.pack(fill="x", padx=20, pady=8)

            texto = ctk.CTkFrame(
                fila,
                fg_color="transparent",
            )
            texto.pack(side="left", padx=18, pady=14)

            ctk.CTkLabel(
                texto,
                text=titulo,
                font=ctk.CTkFont(size=17, weight="bold"),
            ).pack(anchor="w")

            ctk.CTkLabel(
                texto,
                text=descripcion,
                text_color=COLOR_SECUNDARIO,
            ).pack(anchor="w")

            self.crear_boton(
                fila,
                f"Generar {titulo}",
                comando,
            ).pack(side="right", padx=18)

        ctk.CTkLabel(
            panel,
            text="Los archivos se guardan en la carpeta reportes_generados/",
            text_color=COLOR_SECUNDARIO,
        ).pack(anchor="w", padx=20, pady=20)

    def generar_pdf(self):

        try:
            archivo = self.reportes.exportar_pdf()

            messagebox.showinfo(
                "Reporte generado",
                f"PDF generado correctamente:\n{archivo}",
            )

        except Exception as exc:

            messagebox.showerror(
                "Error",
                str(exc),
            )

    def generar_csv(self):

        try:
            archivos = self.reportes.exportar_csv()

            messagebox.showinfo(
                "Reportes generados",
                "\n".join(archivos),
            )

        except Exception as exc:

            messagebox.showerror(
                "Error",
                str(exc),
            )

    def generar_json(self):

        try:
            archivo = self.reportes.exportar_json()

            messagebox.showinfo(
                "Reporte generado",
                f"JSON generado correctamente:\n{archivo}",
            )

        except Exception as exc:

            messagebox.showerror(
                "Error",
                str(exc),
            )

    # ========================================================
    # CONFIGURACIÓN
    # ========================================================

    def pagina_configuracion(self):

        self.titulo(
            "Configuración",
            "Parámetros del sistema y conexión con servicios",
        )

        panel = ctk.CTkFrame(
            self.content,
            fg_color=COLOR_CARD,
            corner_radius=16,
        )
        panel.pack(fill="x")

        ctk.CTkLabel(
            panel,
            text="Modelo local Ollama",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 5))

        self.modelo_entry = ctk.CTkEntry(
            panel,
            height=40,
        )
        self.modelo_entry.insert(
            0,
            self.classifier.cliente.modelo,
        )
        self.modelo_entry.pack(
            fill="x",
            padx=20,
            pady=5,
        )

        ctk.CTkLabel(
            panel,
            text="Umbral mínimo de confianza",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 5))

        self.confianza_entry = ctk.CTkEntry(
            panel,
            height=40,
        )
        self.confianza_entry.insert(
            0,
            "0.70",
        )
        self.confianza_entry.pack(
            fill="x",
            padx=20,
            pady=5,
        )

        self.crear_boton(
            panel,
            "Guardar configuración",
            self.guardar_configuracion,
        ).pack(anchor="e", padx=20, pady=20)

        estado = ctk.CTkFrame(
            self.content,
            fg_color=COLOR_CARD,
            corner_radius=16,
        )
        estado.pack(fill="x", pady=20)

        ctk.CTkLabel(
            estado,
            text="Diagnóstico",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 10))

        mongo = MongoConnection().ping()
        ollama = self.classifier.cliente.verificar_conexion()

        ctk.CTkLabel(
            estado,
            text=(
                "MongoDB: "
                + ("CONECTADO" if mongo else "NO DISPONIBLE")
            ),
            text_color=COLOR_VERDE if mongo else COLOR_ROJO,
        ).pack(anchor="w", padx=20, pady=5)

        ctk.CTkLabel(
            estado,
            text=(
                "Ollama: "
                + ("CONECTADO" if ollama else "NO DISPONIBLE")
            ),
            text_color=COLOR_VERDE if ollama else COLOR_ROJO,
        ).pack(anchor="w", padx=20, pady=(5, 20))

    def guardar_configuracion(self):

        modelo = self.modelo_entry.get().strip()

        if not modelo:

            messagebox.showwarning(
                "Configuración",
                "Escribe un modelo de Ollama.",
            )
            return

        self.classifier.cliente.modelo = modelo
        self.assistant.cliente.modelo = modelo

        messagebox.showinfo(
            "Configuración",
            f"Modelo configurado: {modelo}",
        )


if __name__ == "__main__":

    app = LogiSmartApp()
    app.mainloop()
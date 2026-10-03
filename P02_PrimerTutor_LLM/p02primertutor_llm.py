import tkinter as tk
from tkinter import scrolledtext, messagebox
import ollama


MODELO = "llama3.2"

historial = []


def preguntar():
    pregunta = entrada.get("1.0", tk.END).strip()

    if not pregunta:
        messagebox.showwarning(
            "Aviso",
            "Escribe una pregunta."
        )
        return

    try:
        respuesta = ollama.chat(
            model=MODELO,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un tutor de programación en Python. "
                        "Explica de forma sencilla, clara y breve. "
                        "Si muestras código, utiliza ejemplos pequeños."
                    )
                },
                {
                    "role": "user",
                    "content": pregunta
                }
            ]
        )

        texto = respuesta["message"]["content"]

        historial.append({
            "pregunta": pregunta,
            "respuesta": texto
        })

        chat.insert(
            tk.END,
            f"\nTú:\n{pregunta}\n"
        )

        chat.insert(
            tk.END,
            f"\nTutor:\n{texto}\n"
        )

        chat.insert(
            tk.END,
            "\n" + "-" * 60 + "\n"
        )

        entrada.delete("1.0", tk.END)

    except Exception as e:
        messagebox.showerror(
            "Error",
            f"No se pudo conectar con Ollama.\n\n{e}"
        )


def mostrar_historial():
    if not historial:
        messagebox.showinfo(
            "Historial",
            "Todavía no existen preguntas en el historial."
        )
        return

    resumen = f"Preguntas realizadas: {len(historial)}\n\n"

    for i, registro in enumerate(historial, start=1):
        pregunta = registro["pregunta"]

        if len(pregunta) > 80:
            pregunta = pregunta[:80] + "..."

        resumen += f"{i}. {pregunta}\n"

    messagebox.showinfo(
        "Resumen del historial",
        resumen
    )


def limpiar():
    chat.delete("1.0", tk.END)


# =========================
# INTERFAZ GRÁFICA
# =========================

ventana = tk.Tk()

ventana.title(
    "Tutor de Python con LLM"
)

ventana.geometry(
    "850x650"
)

ventana.configure(
    bg="#202124"
)


titulo = tk.Label(
    ventana,
    text="Tutor de Python con LLM",
    font=("Arial", 22, "bold"),
    bg="#202124",
    fg="white"
)

titulo.pack(
    pady=15
)


subtitulo = tk.Label(
    ventana,
    text="Realiza preguntas y recibe explicaciones usando Ollama",
    font=("Arial", 11),
    bg="#202124",
    fg="#bdbdbd"
)

subtitulo.pack()


chat = scrolledtext.ScrolledText(
    ventana,
    width=90,
    height=25,
    font=("Arial", 10),
    bg="#303134",
    fg="white",
    insertbackground="white",
    wrap=tk.WORD
)

chat.pack(
    padx=20,
    pady=15,
    fill=tk.BOTH,
    expand=True
)


entrada = tk.Text(
    ventana,
    height=4,
    font=("Arial", 11),
    bg="#303134",
    fg="white",
    insertbackground="white",
    wrap=tk.WORD
)

entrada.pack(
    padx=20,
    pady=5,
    fill=tk.X
)


botones = tk.Frame(
    ventana,
    bg="#202124"
)

botones.pack(
    pady=10
)


btn_preguntar = tk.Button(
    botones,
    text="Preguntar",
    command=preguntar,
    width=15,
    bg="#4CAF50",
    fg="white",
    font=("Arial", 10, "bold")
)

btn_preguntar.grid(
    row=0,
    column=0,
    padx=5
)


btn_historial = tk.Button(
    botones,
    text="Ver historial",
    command=mostrar_historial,
    width=15,
    bg="#2196F3",
    fg="white",
    font=("Arial", 10, "bold")
)

btn_historial.grid(
    row=0,
    column=1,
    padx=5
)


btn_limpiar = tk.Button(
    botones,
    text="Limpiar",
    command=limpiar,
    width=15,
    bg="#555555",
    fg="white",
    font=("Arial", 10, "bold")
)

btn_limpiar.grid(
    row=0,
    column=2,
    padx=5
)


ventana.mainloop()
"""
Registro central de skills de Jarvis.

Cada skill devuelve un dict: {"mensaje": str, "dato": Any}
- "mensaje" es lo que Jarvis puede decir en voz alta.
- "dato" es información reusable por un paso siguiente en un comando encadenado
  (ej: la lista de archivos encontrados, para que el siguiente paso pueda abrir uno).
"""

import os
import subprocess
import psutil


def abrir_aplicacion(nombre: str) -> dict:
    """Abre una aplicación conocida por su nombre común."""
    apps_conocidas = {
        "calculadora": "calc.exe",
        "bloc de notas": "notepad.exe",
        "explorador": "explorer.exe",
        "chrome": "chrome.exe",
        "spotify": "spotify.exe",
    }

    ejecutable = apps_conocidas.get(nombre.lower())
    if not ejecutable:
        return {"mensaje": f"No conozco una aplicación llamada '{nombre}' todavía.", "dato": None}

    try:
        os.startfile(ejecutable)
        return {"mensaje": f"Abriendo {nombre}.", "dato": None}
    except OSError:
        return {"mensaje": f"No pude abrir {nombre}: no la encontré en el sistema.", "dato": None}


def abrir_archivo(ruta: str) -> dict:
    """Abre un archivo por su ruta completa, con el programa asociado."""
    if not ruta or not os.path.exists(ruta):
        return {"mensaje": f"No pude abrir el archivo, la ruta '{ruta}' no existe.", "dato": None}

    try:
        os.startfile(ruta)
        nombre_archivo = os.path.basename(ruta)
        return {"mensaje": f"Abriendo {nombre_archivo}.", "dato": ruta}
    except OSError as e:
        return {"mensaje": f"No pude abrir el archivo: {e}", "dato": None}


def procesos_mas_pesados(cantidad: int = 5) -> dict:
    """Devuelve los procesos que más CPU/RAM están usando."""
    procesos = []
    for proc in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
        try:
            procesos.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    top = sorted(procesos, key=lambda p: p["memory_percent"], reverse=True)[:cantidad]

    lineas = [f"{p['name']}: {p['memory_percent']:.1f}% de RAM" for p in top]
    mensaje = "Los procesos que más RAM consumen son: " + "; ".join(lineas)
    return {"mensaje": mensaje, "dato": [p["name"] for p in top]}


def buscar_archivos(nombre: str, carpeta_raiz: str = None) -> dict:
    """Busca archivos por nombre (parcial) dentro de una carpeta."""
    if carpeta_raiz is None:
        carpeta_raiz = os.path.expanduser("~")

    encontrados = []
    for root, _, files in os.walk(carpeta_raiz):
        for f in files:
            if nombre.lower() in f.lower():
                encontrados.append(os.path.join(root, f))
        if len(encontrados) >= 10:
            break

    if not encontrados:
        return {"mensaje": f"No encontré archivos con '{nombre}' en {carpeta_raiz}.", "dato": []}

    mensaje = f"Encontré {len(encontrados)} archivo(s): " + "; ".join(encontrados[:5])
    return {"mensaje": mensaje, "dato": encontrados}


SKILLS = {
    "abrir_aplicacion": {
        "funcion": abrir_aplicacion,
        "descripcion": "Abre una aplicación del sistema por su nombre.",
        "parametros": {"nombre": "string - nombre de la app, ej: 'calculadora'"},
    },
    "abrir_archivo": {
        "funcion": abrir_archivo,
        "descripcion": "Abre un archivo específico por su ruta completa. Usar cuando el usuario quiere abrir algo que se encontró en un paso anterior (ej: 'buscá X y abrilo').",
        "parametros": {"ruta": "string - ruta completa del archivo. Usar '$anterior' si se refiere al resultado del paso previo."},
    },
    "procesos_mas_pesados": {
        "funcion": procesos_mas_pesados,
        "descripcion": "Lista los procesos que más RAM están consumiendo.",
        "parametros": {"cantidad": "int (opcional) - cuántos procesos mostrar"},
    },
    "buscar_archivos": {
        "funcion": buscar_archivos,
        "descripcion": "Busca archivos por nombre en una carpeta.",
        "parametros": {
            "nombre": "string - texto a buscar en el nombre del archivo",
            "carpeta_raiz": "string (opcional) - carpeta donde buscar",
        },
    },
}


def ejecutar_skill(nombre_skill: str, **kwargs) -> dict:
    """Punto único de entrada para ejecutar cualquier skill por nombre."""
    skill = SKILLS.get(nombre_skill)
    if not skill:
        return {"mensaje": f"No existe una skill llamada '{nombre_skill}'.", "dato": None}

    try:
        return skill["funcion"](**kwargs)
    except Exception as e:
        return {"mensaje": f"Error ejecutando {nombre_skill}: {e}", "dato": None}
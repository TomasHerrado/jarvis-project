"""
Registro central de skills de Jarvis.

Cada skill es una función que recibe argumentos con nombre (kwargs) y
devuelve un string con el resultado, para que Jarvis lo pueda decir en voz alta.

El diccionario SKILLS mapea nombre_de_skill -> función, y también guarda
una descripción y el esquema de parámetros esperados. Este esquema es lo
que en la Etapa 3 le vamos a pasar al LLM para que sepa qué puede llamar.
"""

import subprocess
import psutil


def abrir_aplicacion(nombre: str) -> str:
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
        return f"No conozco una aplicación llamada '{nombre}' todavía."

    try:
        subprocess.Popen(ejecutable, shell=True)
        return f"Abriendo {nombre}."
    except Exception as e:
        return f"No pude abrir {nombre}: {e}"


def procesos_mas_pesados(cantidad: int = 5) -> str:
    """Devuelve los procesos que más CPU/RAM están usando."""
    procesos = []
    for proc in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
        try:
            procesos.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    top = sorted(procesos, key=lambda p: p["memory_percent"], reverse=True)[:cantidad]

    lineas = [
        f"{p['name']}: {p['memory_percent']:.1f}% de RAM"
        for p in top
    ]
    return "Los procesos que más RAM consumen son: " + "; ".join(lineas)


def buscar_archivos(nombre: str, carpeta_raiz: str = None) -> str:
    """Busca archivos por nombre (parcial) dentro de una carpeta."""
    import os

    if carpeta_raiz is None:
        carpeta_raiz = os.path.expanduser("~")  # carpeta del usuario por defecto

    encontrados = []
    for root, _, files in os.walk(carpeta_raiz):
        for f in files:
            if nombre.lower() in f.lower():
                encontrados.append(os.path.join(root, f))
        if len(encontrados) >= 10:  # cortamos para no tardar una eternidad
            break

    if not encontrados:
        return f"No encontré archivos con '{nombre}' en {carpeta_raiz}."

    return f"Encontré {len(encontrados)} archivo(s): " + "; ".join(encontrados[:5])


# Registro de skills disponibles.
# El "schema" describe los parámetros para que, más adelante, el LLM
# pueda generar la llamada correcta a partir de lenguaje natural.
SKILLS = {
    "abrir_aplicacion": {
        "funcion": abrir_aplicacion,
        "descripcion": "Abre una aplicación del sistema por su nombre.",
        "parametros": {"nombre": "string - nombre de la app, ej: 'calculadora'"},
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


def ejecutar_skill(nombre_skill: str, **kwargs) -> str:
    """Punto único de entrada para ejecutar cualquier skill por nombre."""
    skill = SKILLS.get(nombre_skill)
    if not skill:
        return f"No existe una skill llamada '{nombre_skill}'."

    try:
        return skill["funcion"](**kwargs)
    except Exception as e:
        return f"Error ejecutando {nombre_skill}: {e}"
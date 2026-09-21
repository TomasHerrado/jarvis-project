"""
Registro central de skills de Jarvis.
Cada skill devuelve un dict: {"mensaje": str, "dato": Any}
"""

import os
import ctypes
import datetime
import shutil
import subprocess
import webbrowser
import psutil
import pyautogui
import pyperclip
import pygetwindow as gw
import screen_brightness_control as sbc
from send2trash import send2trash

APPS_CONOCIDAS = {
    "calculadora": "calc.exe",
    "bloc de notas": "notepad.exe",
    "explorador": "explorer.exe",
    "chrome": "chrome.exe",
    "spotify": "spotify.exe",
}


# --- Aplicaciones y archivos ---

def abrir_aplicacion(nombre: str) -> dict:
    ejecutable = APPS_CONOCIDAS.get(nombre.lower())
    if not ejecutable:
        return {"mensaje": f"No conozco una aplicación llamada '{nombre}' todavía.", "dato": None}
    try:
        os.startfile(ejecutable)
        return {"mensaje": f"Abriendo {nombre}.", "dato": None}
    except OSError:
        return {"mensaje": f"No pude abrir {nombre}: no la encontré en el sistema.", "dato": None}


def cerrar_aplicacion(nombre: str) -> dict:
    ejecutable = APPS_CONOCIDAS.get(nombre.lower())
    if not ejecutable:
        return {"mensaje": f"No conozco una aplicación llamada '{nombre}' todavía.", "dato": None}

    cerrado = False
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() == ejecutable.lower():
                proc.terminate()
                cerrado = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if cerrado:
        return {"mensaje": f"Cerré {nombre}.", "dato": None}
    return {"mensaje": f"No encontré {nombre} abierto.", "dato": None}


def abrir_archivo(ruta: str) -> dict:
    if not ruta or not os.path.exists(ruta):
        return {"mensaje": f"No pude abrir el archivo, la ruta '{ruta}' no existe.", "dato": None}
    try:
        os.startfile(ruta)
        return {"mensaje": f"Abriendo {os.path.basename(ruta)}.", "dato": ruta}
    except OSError as e:
        return {"mensaje": f"No pude abrir el archivo: {e}", "dato": None}


def buscar_archivos(nombre: str, carpeta_raiz: str = None) -> dict:
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


def crear_carpeta(ruta: str) -> dict:
    try:
        os.makedirs(ruta, exist_ok=True)
        return {"mensaje": f"Creé la carpeta {ruta}.", "dato": ruta}
    except Exception as e:
        return {"mensaje": f"No pude crear la carpeta: {e}", "dato": None}


def mover_archivo(origen: str, destino: str) -> dict:
    if not os.path.exists(origen):
        return {"mensaje": f"No encontré el archivo '{origen}'.", "dato": None}
    try:
        shutil.move(origen, destino)
        return {"mensaje": f"Moví el archivo a {destino}.", "dato": destino}
    except Exception as e:
        return {"mensaje": f"No pude mover el archivo: {e}", "dato": None}


def copiar_archivo(origen: str, destino: str) -> dict:
    if not os.path.exists(origen):
        return {"mensaje": f"No encontré el archivo '{origen}'.", "dato": None}
    try:
        shutil.copy(origen, destino)
        return {"mensaje": f"Copié el archivo a {destino}.", "dato": destino}
    except Exception as e:
        return {"mensaje": f"No pude copiar el archivo: {e}", "dato": None}


def renombrar_archivo(ruta: str, nuevo_nombre: str) -> dict:
    if not os.path.exists(ruta):
        return {"mensaje": f"No encontré el archivo '{ruta}'.", "dato": None}
    try:
        nueva_ruta = os.path.join(os.path.dirname(ruta), nuevo_nombre)
        os.rename(ruta, nueva_ruta)
        return {"mensaje": f"Renombré el archivo a {nuevo_nombre}.", "dato": nueva_ruta}
    except Exception as e:
        return {"mensaje": f"No pude renombrar el archivo: {e}", "dato": None}


def eliminar_archivo(ruta: str) -> dict:
    """Manda el archivo a la Papelera de reciclaje (no es borrado permanente)."""
    if not ruta or not os.path.exists(ruta):
        return {"mensaje": f"No encontré el archivo '{ruta}'.", "dato": None}
    try:
        send2trash(ruta)
        return {"mensaje": f"Envié {os.path.basename(ruta)} a la papelera.", "dato": ruta}
    except Exception as e:
        return {"mensaje": f"No pude eliminar el archivo: {e}", "dato": None}


def vaciar_papelera() -> dict:
    try:
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x00000001 | 0x00000002 | 0x00000004)
        return {"mensaje": "Vacié la papelera de reciclaje.", "dato": None}
    except Exception as e:
        return {"mensaje": f"No pude vaciar la papelera: {e}", "dato": None}


def espacio_disco(unidad: str = "C:\\") -> dict:
    try:
        total, _, libre = shutil.disk_usage(unidad)
        return {
            "mensaje": f"Tenés {libre / (1024**3):.1f} GB libres de {total / (1024**3):.1f} GB totales en {unidad}.",
            "dato": libre / (1024**3),
        }
    except Exception as e:
        return {"mensaje": f"No pude revisar el espacio en disco: {e}", "dato": None}


# --- Ventanas ---

def minimizar_ventana_activa() -> dict:
    ventana = gw.getActiveWindow()
    if not ventana:
        return {"mensaje": "No detecto una ventana activa.", "dato": None}
    ventana.minimize()
    return {"mensaje": f"Minimicé {ventana.title}.", "dato": None}


def maximizar_ventana_activa() -> dict:
    ventana = gw.getActiveWindow()
    if not ventana:
        return {"mensaje": "No detecto una ventana activa.", "dato": None}
    ventana.maximize()
    return {"mensaje": f"Maximicé {ventana.title}.", "dato": None}


def cerrar_ventana_activa() -> dict:
    ventana = gw.getActiveWindow()
    if not ventana:
        return {"mensaje": "No detecto una ventana activa.", "dato": None}
    titulo = ventana.title
    ventana.close()
    return {"mensaje": f"Cerré {titulo}.", "dato": None}


def cambiar_ventana() -> dict:
    pyautogui.hotkey("alt", "tab")
    return {"mensaje": "Cambié de ventana.", "dato": None}


def mostrar_escritorio() -> dict:
    pyautogui.hotkey("win", "d")
    return {"mensaje": "Minimicé todo.", "dato": None}


# --- Sistema ---

def procesos_mas_pesados(cantidad: int = 5) -> dict:
    procesos = []
    for proc in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
        try:
            procesos.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    top = sorted(procesos, key=lambda p: p["memory_percent"], reverse=True)[:cantidad]
    lineas = [f"{p['name']}: {p['memory_percent']:.1f}% de RAM" for p in top]
    return {"mensaje": "Los procesos que más RAM consumen son: " + "; ".join(lineas), "dato": [p["name"] for p in top]}


def cambiar_volumen(accion: str) -> dict:
    accion = accion.lower()
    if "sub" in accion or "aument" in accion:
        for _ in range(5):
            pyautogui.press("volumeup")
        return {"mensaje": "Subí el volumen.", "dato": None}
    if "baj" in accion or "dismin" in accion:
        for _ in range(5):
            pyautogui.press("volumedown")
        return {"mensaje": "Bajé el volumen.", "dato": None}
    if "mut" in accion or "silenci" in accion:
        pyautogui.press("volumemute")
        return {"mensaje": "Silencié el audio.", "dato": None}
    return {"mensaje": "No entendí qué hacer con el volumen.", "dato": None}


def cambiar_brillo(nivel: int) -> dict:
    try:
        sbc.set_brightness(nivel)
        return {"mensaje": f"Puse el brillo al {nivel} por ciento.", "dato": nivel}
    except Exception as e:
        return {"mensaje": f"No pude cambiar el brillo: {e}", "dato": None}


def control_multimedia(accion: str) -> dict:
    accion = accion.lower()
    if "pausa" in accion or "play" in accion or "reprod" in accion:
        pyautogui.press("playpause")
        return {"mensaje": "Play/pausa.", "dato": None}
    if "siguiente" in accion or "próxima" in accion or "proxima" in accion:
        pyautogui.press("nexttrack")
        return {"mensaje": "Pasé a la siguiente canción.", "dato": None}
    if "anterior" in accion:
        pyautogui.press("prevtrack")
        return {"mensaje": "Volví a la canción anterior.", "dato": None}
    return {"mensaje": "No entendí qué acción multimedia hacer.", "dato": None}


def bloquear_pantalla() -> dict:
    ctypes.windll.user32.LockWorkStation()
    return {"mensaje": "Bloqueando la pantalla.", "dato": None}


def estado_bateria() -> dict:
    bateria = psutil.sensors_battery()
    if bateria is None:
        return {"mensaje": "No detecto batería en esta máquina.", "dato": None}
    estado = "cargando" if bateria.power_plugged else "sin cargador"
    return {"mensaje": f"La batería está al {bateria.percent:.0f} por ciento, {estado}.", "dato": bateria.percent}


def decir_hora() -> dict:
    ahora = datetime.datetime.now().strftime("%H:%M")
    return {"mensaje": f"Son las {ahora}.", "dato": ahora}


def decir_fecha() -> dict:
    ahora = datetime.datetime.now().strftime("%d/%m/%Y")
    return {"mensaje": f"Hoy es {ahora}.", "dato": ahora}


def apagar_computadora(minutos: int = 1) -> dict:
    segundos = max(int(minutos), 0) * 60
    os.system(f"shutdown /s /t {segundos}")
    return {"mensaje": f"Voy a apagar la computadora en {minutos} minuto(s).", "dato": None}


def cancelar_apagado() -> dict:
    os.system("shutdown /a")
    return {"mensaje": "Cancelé el apagado.", "dato": None}


def reiniciar_computadora(minutos: int = 1) -> dict:
    segundos = max(int(minutos), 0) * 60
    os.system(f"shutdown /r /t {segundos}")
    return {"mensaje": f"Voy a reiniciar la computadora en {minutos} minuto(s).", "dato": None}


# --- Navegador ---

def abrir_url(url: str) -> dict:
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return {"mensaje": f"Abriendo {url}.", "dato": url}


def buscar_en_google(consulta: str) -> dict:
    url = f"https://www.google.com/search?q={consulta.replace(' ', '+')}"
    webbrowser.open(url)
    return {"mensaje": f"Busqué '{consulta}' en Google.", "dato": url}


# --- Portapapeles y notas ---

def copiar_al_portapapeles(texto: str) -> dict:
    pyperclip.copy(texto)
    return {"mensaje": "Lo copié al portapapeles.", "dato": texto}


def leer_portapapeles() -> dict:
    contenido = pyperclip.paste()
    if not contenido:
        return {"mensaje": "El portapapeles está vacío.", "dato": None}
    resumen = contenido if len(contenido) < 200 else contenido[:200] + "..."
    return {"mensaje": f"El portapapeles tiene: {resumen}", "dato": contenido}


def tomar_nota(texto: str) -> dict:
    ruta_notas = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "database", "notas.txt"
    )
    ruta_notas = os.path.abspath(ruta_notas)
    with open(ruta_notas, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}] {texto}\n")
    return {"mensaje": "Anoté eso.", "dato": texto}


def capturar_pantalla() -> dict:
    carpeta_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    nombre_archivo = f"captura_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    ruta = os.path.join(carpeta_desktop, nombre_archivo)
    pyautogui.screenshot().save(ruta)
    return {"mensaje": f"Capturé la pantalla, la guardé en el escritorio como {nombre_archivo}.", "dato": ruta}


def abrir_editor_en_carpeta(ruta: str) -> dict:
    if not ruta or not os.path.isdir(ruta):
        return {"mensaje": f"La carpeta '{ruta}' no existe.", "dato": None}
    try:
        subprocess.Popen(["code", ruta], shell=True)
        return {"mensaje": f"Abriendo el editor en {ruta}.", "dato": ruta}
    except Exception as e:
        return {"mensaje": f"No pude abrir el editor: {e}", "dato": None}


SKILLS = {
    "abrir_aplicacion": {"funcion": abrir_aplicacion, "descripcion": "Abre una aplicación del sistema por su nombre.", "parametros": {"nombre": "string"}},
    "cerrar_aplicacion": {"funcion": cerrar_aplicacion, "descripcion": "Cierra una aplicación abierta por su nombre.", "parametros": {"nombre": "string"}},
    "abrir_archivo": {"funcion": abrir_archivo, "descripcion": "Abre un archivo por su ruta completa. Usar '$anterior' si se refiere a un resultado previo.", "parametros": {"ruta": "string"}},
    "buscar_archivos": {"funcion": buscar_archivos, "descripcion": "Busca archivos por nombre en una carpeta.", "parametros": {"nombre": "string", "carpeta_raiz": "string (opcional)"}},
    "crear_carpeta": {"funcion": crear_carpeta, "descripcion": "Crea una carpeta en la ruta indicada.", "parametros": {"ruta": "string"}},
    "mover_archivo": {"funcion": mover_archivo, "descripcion": "Mueve un archivo de una ruta a otra.", "parametros": {"origen": "string", "destino": "string"}},
    "copiar_archivo": {"funcion": copiar_archivo, "descripcion": "Copia un archivo a otra ruta.", "parametros": {"origen": "string", "destino": "string"}},
    "renombrar_archivo": {"funcion": renombrar_archivo, "descripcion": "Renombra un archivo.", "parametros": {"ruta": "string", "nuevo_nombre": "string"}},
    "eliminar_archivo": {"funcion": eliminar_archivo, "descripcion": "Manda un archivo a la papelera de reciclaje. ACCIÓN SENSIBLE, requiere confirmación.", "parametros": {"ruta": "string"}, "requiere_confirmacion": True},
    "vaciar_papelera": {"funcion": vaciar_papelera, "descripcion": "Vacía la papelera de reciclaje de Windows. ACCIÓN SENSIBLE, requiere confirmación.", "parametros": {}, "requiere_confirmacion": True},
    "espacio_disco": {"funcion": espacio_disco, "descripcion": "Dice el espacio libre en disco.", "parametros": {"unidad": "string (opcional, ej: 'C:\\\\')"}},
    "minimizar_ventana_activa": {"funcion": minimizar_ventana_activa, "descripcion": "Minimiza la ventana actualmente en foco.", "parametros": {}},
    "maximizar_ventana_activa": {"funcion": maximizar_ventana_activa, "descripcion": "Maximiza la ventana actualmente en foco.", "parametros": {}},
    "cerrar_ventana_activa": {"funcion": cerrar_ventana_activa, "descripcion": "Cierra la ventana actualmente en foco.", "parametros": {}},
    "cambiar_ventana": {"funcion": cambiar_ventana, "descripcion": "Cambia a la siguiente ventana (alt+tab).", "parametros": {}},
    "mostrar_escritorio": {"funcion": mostrar_escritorio, "descripcion": "Minimiza todas las ventanas para mostrar el escritorio.", "parametros": {}},
    "procesos_mas_pesados": {"funcion": procesos_mas_pesados, "descripcion": "Lista los procesos que más RAM están consumiendo.", "parametros": {"cantidad": "int (opcional)"}},
    "cambiar_volumen": {"funcion": cambiar_volumen, "descripcion": "Sube, baja o silencia el volumen del sistema.", "parametros": {"accion": "string - 'subir', 'bajar' o 'mutear'"}},
    "cambiar_brillo": {"funcion": cambiar_brillo, "descripcion": "Cambia el brillo de la pantalla.", "parametros": {"nivel": "int - porcentaje de 0 a 100"}},
    "control_multimedia": {"funcion": control_multimedia, "descripcion": "Controla la reproducción multimedia: play/pausa, siguiente, anterior.", "parametros": {"accion": "string"}},
    "bloquear_pantalla": {"funcion": bloquear_pantalla, "descripcion": "Bloquea la pantalla de Windows.", "parametros": {}},
    "estado_bateria": {"funcion": estado_bateria, "descripcion": "Dice el porcentaje de batería actual.", "parametros": {}},
    "decir_hora": {"funcion": decir_hora, "descripcion": "Dice la hora actual.", "parametros": {}},
    "decir_fecha": {"funcion": decir_fecha, "descripcion": "Dice la fecha actual.", "parametros": {}},
    "apagar_computadora": {"funcion": apagar_computadora, "descripcion": "Apaga la computadora. ACCIÓN SENSIBLE, requiere confirmación.", "parametros": {"minutos": "int (opcional)"}, "requiere_confirmacion": True},
    "cancelar_apagado": {"funcion": cancelar_apagado, "descripcion": "Cancela un apagado o reinicio programado.", "parametros": {}},
    "reiniciar_computadora": {"funcion": reiniciar_computadora, "descripcion": "Reinicia la computadora. ACCIÓN SENSIBLE, requiere confirmación.", "parametros": {"minutos": "int (opcional)"}, "requiere_confirmacion": True},
    "abrir_url": {"funcion": abrir_url, "descripcion": "Abre una URL específica en el navegador.", "parametros": {"url": "string"}},
    "buscar_en_google": {"funcion": buscar_en_google, "descripcion": "Busca algo en Google.", "parametros": {"consulta": "string"}},
    "copiar_al_portapapeles": {"funcion": copiar_al_portapapeles, "descripcion": "Copia un texto al portapapeles.", "parametros": {"texto": "string"}},
    "leer_portapapeles": {"funcion": leer_portapapeles, "descripcion": "Lee qué hay en el portapapeles.", "parametros": {}},
    "tomar_nota": {"funcion": tomar_nota, "descripcion": "Guarda una nota de texto dictada.", "parametros": {"texto": "string"}},
    "capturar_pantalla": {"funcion": capturar_pantalla, "descripcion": "Toma una captura de pantalla y la guarda en el escritorio.", "parametros": {}},
    "abrir_editor_en_carpeta": {"funcion": abrir_editor_en_carpeta, "descripcion": "Abre VS Code en una carpeta específica.", "parametros": {"ruta": "string"}},
}


def ejecutar_skill(nombre_skill: str, **kwargs) -> dict:
    skill = SKILLS.get(nombre_skill)
    if not skill:
        return {"mensaje": f"No existe una skill llamada '{nombre_skill}'.", "dato": None}
    try:
        return skill["funcion"](**kwargs)
    except Exception as e:
        return {"mensaje": f"Error ejecutando {nombre_skill}: {e}", "dato": None}
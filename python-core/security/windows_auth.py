"""
Verificación de identidad validando la contraseña real de Windows del
usuario actual, contra el sistema operativo (no un chequeo simulado).
"""

import ctypes
import getpass
import os
import tkinter as tk
from tkinter import simpledialog

LOGON32_LOGON_INTERACTIVE = 2
LOGON32_PROVIDER_DEFAULT = 0


def _pedir_password_gui() -> str:
    """Abre una ventanita para pedir la contraseña, con el texto oculto."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    password = simpledialog.askstring(
        "Verificación de Jarvis",
        "Ingresá tu contraseña de Windows:",
        show="*",
        parent=root,
    )
    root.destroy()
    return password or ""


def confirmar_con_password_windows() -> bool:
    """Pide la contraseña de Windows en una ventana y la valida contra el sistema."""
    usuario = getpass.getuser()
    dominio = os.environ.get("USERDOMAIN", ".")

    password = _pedir_password_gui()
    if not password:
        return False

    handle_token = ctypes.c_void_p()
    resultado = ctypes.windll.advapi32.LogonUserW(
        usuario,
        dominio,
        password,
        LOGON32_LOGON_INTERACTIVE,
        LOGON32_PROVIDER_DEFAULT,
        ctypes.byref(handle_token),
    )

    if resultado:
        ctypes.windll.kernel32.CloseHandle(handle_token)
        return True
    return False


if __name__ == "__main__":
    print("Probando validación de contraseña de Windows...")
    exito = confirmar_con_password_windows()
    print(f"¿Verificado? {exito}")
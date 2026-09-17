"""
Capa de persistencia de Jarvis: historial de conversaciones y preferencias.
La base vive en database/jarvis.db (carpeta ya creada en la Etapa 0).
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "database", "jarvis.db"
)
DB_PATH = os.path.abspath(DB_PATH)


def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_db():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            texto_usuario TEXT NOT NULL,
            skill_ejecutada TEXT,
            params TEXT,
            respuesta TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preferencias (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def guardar_interaccion(texto_usuario, skill_ejecutada, params, respuesta):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO conversaciones (timestamp, texto_usuario, skill_ejecutada, params, respuesta)
           VALUES (?, ?, ?, ?, ?)""",
        (datetime.now().isoformat(), texto_usuario, skill_ejecutada, str(params), respuesta),
    )
    conn.commit()
    conn.close()


def obtener_historial_reciente(cantidad=5):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conversaciones ORDER BY id DESC LIMIT ?", (cantidad,))
    filas = cursor.fetchall()
    conn.close()
    return [dict(fila) for fila in reversed(filas)]


def set_preferencia(clave, valor):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO preferencias (clave, valor) VALUES (?, ?)
           ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor""",
        (clave, valor),
    )
    conn.commit()
    conn.close()


def get_preferencia(clave, default=None):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM preferencias WHERE clave = ?", (clave,))
    fila = cursor.fetchone()
    conn.close()
    return fila["valor"] if fila else default
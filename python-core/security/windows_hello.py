"""
Verificación de identidad usando Windows Hello (cara, huella o PIN),
para autorizar acciones sensibles de Jarvis sin depender de una palabra clave.
"""

import asyncio
from winsdk.windows.security.credentials.ui import (
    UserConsentVerifier,
    UserConsentVerifierAvailability,
    UserConsentVerificationResult,
)


async def _verificar_disponibilidad():
    return await UserConsentVerifier.check_availability_async()


async def _pedir_verificacion(mensaje: str):
    return await UserConsentVerifier.request_verification_async(mensaje)


def hay_windows_hello_disponible() -> bool:
    disponibilidad = asyncio.run(_verificar_disponibilidad())
    return disponibilidad == UserConsentVerifierAvailability.AVAILABLE


def confirmar_con_windows_hello(mensaje: str = "Confirmá esta acción en Jarvis") -> bool:
    """Dispara el prompt nativo de Windows (cara/huella/PIN). Devuelve True solo si se verificó con éxito."""
    resultado = asyncio.run(_pedir_verificacion(mensaje))
    return resultado == UserConsentVerificationResult.VERIFIED


if __name__ == "__main__":
    disponibilidad = asyncio.run(_verificar_disponibilidad())
    print(f"Disponibilidad de Windows Hello: {disponibilidad}")

    if disponibilidad == UserConsentVerifierAvailability.AVAILABLE:
        print("Disparando el prompt de verificación...")
        exito = confirmar_con_windows_hello("Prueba de Jarvis: confirmá tu identidad")
        print(f"¿Verificado? {exito}")
    else:
        print("Windows Hello no está disponible/configurado en esta máquina.")
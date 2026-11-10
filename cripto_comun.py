"""
Núcleo criptográfico compartido por todos los scripts.

Cifrado con contraseña = scrypt (derivación de clave, lento a propósito para
frenar fuerza bruta) + AES-256-GCM (cifrado autenticado: si alguien toca un
solo bit, o la contraseña es incorrecta, el descifrado falla en vez de
devolver basura).

Formato del blob:  MAGIA(3) | salt(16) | nonce(12) | ciphertext+tag(16)
"""

import getpass
import os
import sys

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

MAGIA = b"CK1"
_SALT = 16
_NONCE = 12
SOBRECARGA = len(MAGIA) + _SALT + _NONCE + 16  # bytes extra que agrega cifrar()


class ErrorDescifrado(Exception):
    """Contraseña incorrecta o datos manipulados/corruptos."""


def derivar_clave(password: str, salt: bytes) -> bytes:
    # n=2**15 -> ~32 MB de RAM y ~0.1 s por intento: barato para vos, caro
    # para quien prueba millones de contraseñas.
    kdf = Scrypt(salt=salt, length=32, n=2**15, r=8, p=1)
    return kdf.derive(password.encode("utf-8"))


def cifrar(datos: bytes, password: str) -> bytes:
    salt = os.urandom(_SALT)
    nonce = os.urandom(_NONCE)
    clave = derivar_clave(password, salt)
    return MAGIA + salt + nonce + AESGCM(clave).encrypt(nonce, datos, MAGIA)


def descifrar(blob: bytes, password: str) -> bytes:
    if len(blob) < SOBRECARGA or not blob.startswith(MAGIA):
        raise ErrorDescifrado("Los datos no tienen el formato esperado.")
    i = len(MAGIA)
    salt = blob[i:i + _SALT]
    nonce = blob[i + _SALT:i + _SALT + _NONCE]
    ct = blob[i + _SALT + _NONCE:]
    clave = derivar_clave(password, salt)
    try:
        return AESGCM(clave).decrypt(nonce, ct, MAGIA)
    except InvalidTag:
        raise ErrorDescifrado("Contraseña incorrecta o datos alterados.") from None


def pedir_password(confirmar: bool = False) -> str:
    """Pide la contraseña sin mostrarla en pantalla (ni en el historial)."""
    while True:
        p = getpass.getpass("Contraseña: ")
        if not p:
            print("La contraseña no puede estar vacía.", file=sys.stderr)
            continue
        if confirmar and getpass.getpass("Repetila: ") != p:
            print("No coinciden, otra vez.", file=sys.stderr)
            continue
        return p


def morir(msg: str, codigo: int = 1):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(codigo)

#!/usr/bin/env python3
"""
02 · CIFRADO CON EMOJIS 😂🐸🍕
Convierte tu mensaje en una sopa de emojis que podés pegar en cualquier chat.
Por dentro es AES-256-GCM de verdad: cada byte del texto cifrado se dibuja
como uno de 256 emojis. Sin la contraseña es indescifrable (no es un
"reemplazo de letras" que se rompe en 5 minutos).

Ejemplos:
  python 02_cifrado_emojis.py cifrar "Nos vemos a las 9 en la plaza"
  python 02_cifrado_emojis.py descifrar "😀🐸🍕..."
  python 02_cifrado_emojis.py cifrar "hola" --sin-clave   # solo codifica, NO es seguro

Limitaciones:
  - El resultado es largo: ~31 emojis de sobrecarga + 1 emoji por byte.
  - Usa emojis de un solo código Unicode para que no se rompan al copiar,
    pero alguna app vieja puede mostrar alguno como un cuadradito.
"""

import argparse
import sys

from cripto_comun import ErrorDescifrado, cifrar, descifrar, morir, pedir_password

# 80 caritas (U+1F600–1F64F) + 176 animales/comida/objetos (U+1F400–1F4AF) = 256
EMOJIS = [chr(c) for c in range(0x1F600, 0x1F650)] + [chr(c) for c in range(0x1F400, 0x1F4B0)]
assert len(EMOJIS) == 256 and len(set(EMOJIS)) == 256
A_BYTE = {e: i for i, e in enumerate(EMOJIS)}
PREFIJO_PLANO = "🔓"  # marca de "solo codificado, sin contraseña"
IGNORAR = set(" \n\r\t️‍")


def bytes_a_emojis(b: bytes) -> str:
    return "".join(EMOJIS[x] for x in b)


def emojis_a_bytes(s: str) -> bytes:
    out = bytearray()
    for ch in s:
        if ch in IGNORAR:
            continue
        if ch not in A_BYTE:
            raise ValueError(f"Emoji desconocido: {ch!r} (¿se cortó al copiar?)")
        out.append(A_BYTE[ch])
    return bytes(out)


def main():
    ap = argparse.ArgumentParser(description="Cifra mensajes como emojis.")
    ap.add_argument("modo", choices=["cifrar", "descifrar"])
    ap.add_argument("texto", nargs="?", help="si se omite, se lee de stdin")
    ap.add_argument("--clave")
    ap.add_argument("--sin-clave", action="store_true",
                    help="solo codifica en emojis (cualquiera con este script lo lee)")
    a = ap.parse_args()
    texto = a.texto if a.texto is not None else sys.stdin.read()

    if a.modo == "cifrar":
        datos = texto.encode("utf-8")
        if a.sin_clave:
            print(PREFIJO_PLANO + bytes_a_emojis(datos))
        else:
            pwd = a.clave or pedir_password(confirmar=True)
            print(bytes_a_emojis(cifrar(datos, pwd)))
        return

    texto = texto.strip()
    try:
        if texto.startswith(PREFIJO_PLANO):
            print(emojis_a_bytes(texto[len(PREFIJO_PLANO):]).decode("utf-8"))
            return
        blob = emojis_a_bytes(texto)
        print(descifrar(blob, a.clave or pedir_password()).decode("utf-8"))
    except (ValueError, ErrorDescifrado) as e:
        morir(str(e))


if __name__ == "__main__":
    main()

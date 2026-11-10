#!/usr/bin/env python3
"""
03 · TINTA INVISIBLE DIGITAL 👻
Esconde un mensaje secreto DENTRO de un texto normal usando caracteres
Unicode de ancho cero (no se ven, pero viajan cuando copiás y pegás).

  "Che, ¿mañana jugamos al fútbol?"   <- lo que ve todo el mundo
  "el profe de mate es un robot"        <- lo que hay escondido adentro

También sirve al revés (y esto es MUY útil): `detectar` te dice si un texto
que te pasaron trae caracteres invisibles. Algunas empresas y "detectores
de IA" marcan textos así para rastrear quién filtró qué.

Ejemplos:
  python 03_texto_invisible.py ocultar "Che, ¿mañana jugamos?" "el profe es un robot"
  python 03_texto_invisible.py ocultar "Texto inocente" "secreto" --cifrar
  python 03_texto_invisible.py revelar < mensaje.txt
  python 03_texto_invisible.py detectar < texto_sospechoso.txt
  python 03_texto_invisible.py limpiar < texto.txt > limpio.txt

Limitaciones: algunas plataformas (ciertos foros, SMS, algunos editores)
borran los caracteres de ancho cero. WhatsApp, Telegram, Discord y la
mayoría de los mails los conservan. Las terminales a veces los muestran
raros: para revelar, conviene pasar el texto por un archivo/stdin.
"""

import argparse
import sys
import unicodedata

from cripto_comun import ErrorDescifrado, cifrar, descifrar, morir, pedir_password

CERO, UNO = "​", "‌"          # zero-width space / non-joiner
INICIO, FIN = "⁠", "⁣"        # word joiner / invisible separator
FLAG_PLANO, FLAG_CIFRADO = 0, 1

# Caracteres invisibles o engañosos que vale la pena detectar
SOSPECHOSOS = {
    "​": "ZERO WIDTH SPACE", "‌": "ZERO WIDTH NON-JOINER",
    "‍": "ZERO WIDTH JOINER", "⁠": "WORD JOINER",
    "⁡": "FUNCTION APPLICATION", "⁢": "INVISIBLE TIMES",
    "⁣": "INVISIBLE SEPARATOR", "⁤": "INVISIBLE PLUS",
    "﻿": "BOM / ZERO WIDTH NO-BREAK SPACE", "᠎": "MONGOLIAN VOWEL SEPARATOR",
    "­": "SOFT HYPHEN", "‮": "RIGHT-TO-LEFT OVERRIDE (¡da vuelta el texto!)",
    "‭": "LEFT-TO-RIGHT OVERRIDE",
}


def a_invisible(datos: bytes) -> str:
    bits = "".join(f"{b:08b}" for b in datos)
    return INICIO + "".join(UNO if x == "1" else CERO for x in bits) + FIN


def de_invisible(texto: str) -> bytes:
    i, j = texto.find(INICIO), texto.find(FIN)
    if i == -1 or j == -1 or j < i:
        raise ValueError("No encontré ningún mensaje invisible en ese texto.")
    bits = "".join("1" if c == UNO else "0" for c in texto[i + 1:j] if c in (CERO, UNO))
    if len(bits) % 8:
        raise ValueError("El mensaje invisible está incompleto (¿se cortó al copiar?).")
    return bytes(int(bits[k:k + 8], 2) for k in range(0, len(bits), 8))


def ocultar(visible: str, secreto: str, password: str | None = None) -> str:
    datos = secreto.encode("utf-8")
    datos = bytes([FLAG_CIFRADO]) + cifrar(datos, password) if password else bytes([FLAG_PLANO]) + datos
    # Lo metemos después del primer carácter: si alguien copia solo una parte
    # del texto, lo más probable es que copie el principio.
    pos = 1 if visible else 0
    return visible[:pos] + a_invisible(datos) + visible[pos:]


def revelar(texto: str, password_cb) -> str:
    datos = de_invisible(texto)
    if datos[0] == FLAG_CIFRADO:
        return descifrar(datos[1:], password_cb()).decode("utf-8")
    return datos[1:].decode("utf-8")


def detectar(texto: str) -> dict:
    conteo = {}
    for ch in texto:
        if ch in SOSPECHOSOS or (unicodedata.category(ch) == "Cf" and ch not in "\n\t"):
            nombre = SOSPECHOSOS.get(ch) or unicodedata.name(ch, f"U+{ord(ch):04X}")
            conteo[nombre] = conteo.get(nombre, 0) + 1
    return conteo


def limpiar(texto: str) -> str:
    return "".join(c for c in texto if not (c in SOSPECHOSOS or unicodedata.category(c) == "Cf"))


def main():
    ap = argparse.ArgumentParser(description="Esconde mensajes invisibles dentro de texto.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("ocultar")
    o.add_argument("visible")
    o.add_argument("secreto")
    o.add_argument("--cifrar", action="store_true")
    o.add_argument("--clave")
    for nombre in ("revelar", "detectar", "limpiar"):
        p = sub.add_parser(nombre)
        p.add_argument("texto", nargs="?", help="si se omite, se lee de stdin")
        if nombre == "revelar":
            p.add_argument("--clave")
    a = ap.parse_args()

    if a.cmd == "ocultar":
        pwd = (a.clave or pedir_password(confirmar=True)) if a.cifrar else None
        resultado = ocultar(a.visible, a.secreto, pwd)
        sys.stdout.write(resultado + "\n")
        print(f"\n👻 Copiá el texto de arriba. Parece normal, pero lleva "
              f"{len(resultado) - len(a.visible)} caracteres invisibles.", file=sys.stderr)
        return

    texto = a.texto if a.texto is not None else sys.stdin.read()
    if a.cmd == "revelar":
        try:
            print("🤫 " + revelar(texto, lambda: a.clave or pedir_password()))
        except (ValueError, ErrorDescifrado) as e:
            morir(str(e))
    elif a.cmd == "detectar":
        encontrados = detectar(texto)
        if not encontrados:
            print("✅ Texto limpio: no hay caracteres invisibles.")
        else:
            print("🚨 ¡Ojo! Este texto trae caracteres invisibles:")
            for nombre, n in sorted(encontrados.items(), key=lambda x: -x[1]):
                print(f"   {n:>5} × {nombre}")
            if INICIO in texto and FIN in texto:
                print("   -> Parece un mensaje de este script. Probá `revelar`.")
    else:
        sys.stdout.write(limpiar(texto))


if __name__ == "__main__":
    main()

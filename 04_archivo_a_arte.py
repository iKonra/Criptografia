#!/usr/bin/env python3
"""
04 · TU ARCHIVO COMO ARTE ABSTRACTO 🎨
Convierte CUALQUIER archivo (PDF, ZIP, MP3, tu tesis...) en una imagen PNG
que parece estática de televisor. Cada píxel guarda 3 bytes del archivo
cifrado. Para recuperarlo, pasás la imagen y la contraseña.

A diferencia del script 01, acá no se esconde nada: la imagen ES el archivo.
Es útil para guardar cosas en lugares que solo aceptan imágenes (la nube de
fotos del celular, un álbum, un fondo de pantalla raro) o para mandarle a
alguien "un cuadro" que en realidad es un documento.

Ejemplos:
  python 04_archivo_a_arte.py codificar tesis.pdf obra_maestra.png
  python 04_archivo_a_arte.py decodificar obra_maestra.png
  python 04_archivo_a_arte.py codificar notas.txt arte.png --sin-cifrar   # ¡ves patrones!

Tip: probá --sin-cifrar con un .txt o un .bmp y vas a ver estructura en la
imagen. Con cifrado se ve ruido puro: así se "ve" un buen cifrado.

Limitaciones: igual que en 01, guardala/mandala siempre como PNG original.
Google Photos en "calidad ahorro" o cualquier recompresión la rompe.
"""

import argparse
import math
import os
import struct

import numpy as np
from PIL import Image

from cripto_comun import ErrorDescifrado, cifrar, descifrar, morir, pedir_password

FIRMA = b"ART1"
FLAG_CIFRADO = 1


def archivo_a_imagen(datos: bytes, nombre: str, password: str | None) -> Image.Image:
    n = nombre.encode("utf-8")[:255]
    cuerpo = bytes([len(n)]) + n + datos
    flags = 0
    if password:
        cuerpo, flags = cifrar(cuerpo, password), FLAG_CIFRADO
    paquete = FIRMA + bytes([flags]) + struct.pack(">I", len(cuerpo)) + cuerpo
    pixeles = math.ceil(len(paquete) / 3)
    lado = max(1, math.ceil(math.sqrt(pixeles)))
    relleno = os.urandom(lado * lado * 3 - len(paquete))  # relleno aleatorio, no ceros
    arr = np.frombuffer(paquete + relleno, dtype=np.uint8).reshape(lado, lado, 3)
    return Image.fromarray(arr, "RGB")


def imagen_a_archivo(img: Image.Image, password_cb) -> tuple[str, bytes]:
    plano = np.array(img.convert("RGB"), dtype=np.uint8).tobytes()
    if not plano.startswith(FIRMA):
        raise ValueError("Esta imagen no fue creada con este script (o fue recomprimida).")
    flags = plano[len(FIRMA)]
    largo = struct.unpack(">I", plano[len(FIRMA) + 1:len(FIRMA) + 5])[0]
    cuerpo = plano[len(FIRMA) + 5:len(FIRMA) + 5 + largo]
    if len(cuerpo) != largo:
        raise ValueError("La imagen está truncada.")
    if flags & FLAG_CIFRADO:
        cuerpo = descifrar(cuerpo, password_cb())
    n = cuerpo[0]
    return cuerpo[1:1 + n].decode("utf-8", "replace"), cuerpo[1 + n:]


def main():
    ap = argparse.ArgumentParser(description="Convierte archivos en imágenes (y viceversa).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("codificar")
    c.add_argument("archivo")
    c.add_argument("salida", help=".png")
    c.add_argument("--sin-cifrar", action="store_true")
    c.add_argument("--clave")
    d = sub.add_parser("decodificar")
    d.add_argument("imagen")
    d.add_argument("-o", "--salida")
    d.add_argument("--clave")
    a = ap.parse_args()

    if a.cmd == "codificar":
        if not a.salida.lower().endswith(".png"):
            morir("La salida tiene que ser .png")
        with open(a.archivo, "rb") as fh:
            datos = fh.read()
        pwd = None if a.sin_cifrar else (a.clave or pedir_password(confirmar=True))
        img = archivo_a_imagen(datos, os.path.basename(a.archivo), pwd)
        img.save(a.salida, "PNG")
        print(f"🎨 '{a.archivo}' ({len(datos):,} bytes) ahora es una obra de "
              f"{img.size[0]}x{img.size[1]} px: {a.salida}")
        return

    try:
        nombre, datos = imagen_a_archivo(Image.open(a.imagen), lambda: a.clave or pedir_password())
    except (ValueError, ErrorDescifrado) as e:
        morir(str(e))
    destino = a.salida or ("recuperado_" + os.path.basename(nombre))
    with open(destino, "wb") as fh:
        fh.write(datos)
    print(f"📂 Recuperado '{nombre}' -> {destino} ({len(datos):,} bytes)")


if __name__ == "__main__":
    main()

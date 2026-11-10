#!/usr/bin/env python3
"""
01 · ESTEGANOGRAFÍA EN IMÁGENES 🖼️🕵️
Esconde un mensaje o un archivo entero dentro de una foto. La foto se ve
igual a simple vista: cambiamos solo el bit menos significativo de cada canal
de color (un cambio de 1/255 en el brillo, imperceptible).

Con --cifrar, el contenido además va cifrado con AES-GCM, así que aunque
alguien sospeche y extraiga los bits, solo ve ruido.

Ejemplos:
  python 01_esteganografia.py ocultar gato.jpg gato_secreto.png -m "La pizza está en el freezer"
  python 01_esteganografia.py ocultar gato.jpg gato_secreto.png -f plan.pdf --cifrar
  python 01_esteganografia.py revelar gato_secreto.png
  python 01_esteganografia.py capacidad gato.jpg

⚠️ Limitaciones reales:
  - La salida DEBE ser PNG (sin pérdida). JPG destruye los bits ocultos.
  - WhatsApp/Instagram/Facebook recomprimen las imágenes -> mensaje perdido.
    Mandala como "documento"/archivo, no como foto.
  - Esto oculta, no hace invisible: un análisis estadístico (steganálisis)
    puede detectar que hay algo. Por eso existe --cifrar.
"""

import argparse
import os
import struct

import numpy as np
from PIL import Image

from cripto_comun import ErrorDescifrado, cifrar, descifrar, morir, pedir_password

FIRMA = b"STG1"
FLAG_CIFRADO = 1
FLAG_ARCHIVO = 2


def _cargar(ruta):
    img = Image.open(ruta)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    return img


def _canales_rgb(arr):
    # Solo usamos R, G, B (nunca alfa: tocar la transparencia se nota).
    return arr[..., :3].reshape(-1)


def capacidad_bytes(img) -> int:
    w, h = img.size
    return (w * h * 3) // 8 - len(FIRMA) - 5  # firma + flags(1) + largo(4)


def armar_payload(datos: bytes, nombre: str | None, password: str | None) -> tuple[int, bytes]:
    flags = 0
    if nombre is not None:
        flags |= FLAG_ARCHIVO
        n = nombre.encode("utf-8")[:255]
        datos = bytes([len(n)]) + n + datos
    if password:
        flags |= FLAG_CIFRADO
        datos = cifrar(datos, password)
    return flags, datos


def ocultar(img, flags: int, datos: bytes):
    arr = np.array(img, dtype=np.uint8)
    plano = _canales_rgb(arr).copy()
    paquete = FIRMA + bytes([flags]) + struct.pack(">I", len(datos)) + datos
    bits = np.unpackbits(np.frombuffer(paquete, dtype=np.uint8))
    if len(bits) > len(plano):
        raise ValueError(
            f"No entra: necesitás {len(paquete)} bytes y la imagen aguanta "
            f"{capacidad_bytes(img) + len(FIRMA) + 5}. Usá una imagen más grande."
        )
    plano[: len(bits)] = (plano[: len(bits)] & 0xFE) | bits
    arr[..., :3] = plano.reshape(arr[..., :3].shape)
    return Image.fromarray(arr, img.mode)


def extraer(img) -> tuple[int, bytes]:
    plano = _canales_rgb(np.array(img, dtype=np.uint8))

    def leer(desde_byte, n):
        bits = plano[desde_byte * 8:(desde_byte + n) * 8] & 1
        return np.packbits(bits).tobytes()

    cab = leer(0, len(FIRMA) + 5)
    if cab[: len(FIRMA)] != FIRMA:
        raise ValueError("Esta imagen no tiene nada escondido (o fue recomprimida).")
    flags = cab[len(FIRMA)]
    largo = struct.unpack(">I", cab[len(FIRMA) + 1:])[0]
    if largo > len(plano) // 8:
        raise ValueError("Cabecera corrupta.")
    return flags, leer(len(cab), largo)


def main():
    ap = argparse.ArgumentParser(description="Esconde mensajes/archivos dentro de imágenes.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    o = sub.add_parser("ocultar")
    o.add_argument("imagen")
    o.add_argument("salida", help="debe terminar en .png")
    g = o.add_mutually_exclusive_group(required=True)
    g.add_argument("-m", "--mensaje")
    g.add_argument("-f", "--archivo")
    o.add_argument("--cifrar", action="store_true", help="cifra con contraseña antes de ocultar")
    o.add_argument("--clave", help="contraseña (si no, se pide sin mostrarla)")

    r = sub.add_parser("revelar")
    r.add_argument("imagen")
    r.add_argument("-o", "--salida", help="dónde guardar si es un archivo")
    r.add_argument("--clave")

    c = sub.add_parser("capacidad")
    c.add_argument("imagen")

    a = ap.parse_args()

    if a.cmd == "capacidad":
        img = _cargar(a.imagen)
        cap = capacidad_bytes(img)
        print(f"📦 {a.imagen} ({img.size[0]}x{img.size[1]}) aguanta ~{cap:,} bytes "
              f"(~{cap // 1024} KB, ~{cap // 2000} páginas de texto).")
        return

    if a.cmd == "ocultar":
        if not a.salida.lower().endswith(".png"):
            morir("La salida tiene que ser .png (JPG destruye el mensaje).")
        if a.mensaje is not None:
            datos, nombre = a.mensaje.encode("utf-8"), None
        else:
            with open(a.archivo, "rb") as fh:
                datos = fh.read()
            nombre = os.path.basename(a.archivo)
        pwd = (a.clave or pedir_password(confirmar=True)) if a.cifrar else None
        flags, payload = armar_payload(datos, nombre, pwd)
        try:
            out = ocultar(_cargar(a.imagen), flags, payload)
        except ValueError as e:
            morir(str(e))
        out.save(a.salida, "PNG")
        print(f"✅ Escondido en {a.salida} ({len(payload):,} bytes). "
              "La imagen se ve idéntica. Mandala como ARCHIVO, no como foto.")
        return

    # revelar
    try:
        flags, datos = extraer(_cargar(a.imagen))
    except ValueError as e:
        morir(str(e))
    if flags & FLAG_CIFRADO:
        try:
            datos = descifrar(datos, a.clave or pedir_password())
        except ErrorDescifrado as e:
            morir(str(e))
    if flags & FLAG_ARCHIVO:
        n = datos[0]
        nombre = datos[1:1 + n].decode("utf-8", "replace")
        contenido = datos[1 + n:]
        destino = a.salida or ("revelado_" + os.path.basename(nombre))
        with open(destino, "wb") as fh:
            fh.write(contenido)
        print(f"📂 Archivo oculto '{nombre}' guardado como {destino} ({len(contenido):,} bytes).")
    else:
        print("🤫 Mensaje oculto:\n")
        print(datos.decode("utf-8", "replace"))


if __name__ == "__main__":
    main()

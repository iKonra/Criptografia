#!/usr/bin/env python3
"""
05 · CRIPTOGRAFÍA VISUAL (Naor–Shamir, 1994) 👓
Parte un mensaje (o una imagen en blanco y negro) en DOS imágenes de ruido.
Cada una por separado es ruido aleatorio puro: matemáticamente no revela
NADA, ni con una supercomputadora (es un one-time pad visual). Pero si las
imprimís en acetato/transparencia y las superponés... aparece el mensaje.
Sin computadora para descifrar: lo descifra tu ojo.

Ideas: invitaciones de cumpleaños en dos partes, búsquedas del tesoro,
proponer casamiento con dos cartas, darle media clave a cada socio.

Ejemplos:
  python 05_criptografia_visual.py dividir --texto "TE AMO" -o carta
      -> carta_A.png y carta_B.png
  python 05_criptografia_visual.py dividir --imagen logo.png -o logo
  python 05_criptografia_visual.py superponer carta_A.png carta_B.png -o revelado.png

Cómo verlo sin imprimir: abrí las dos en un editor (GIMP, Photopea), poné
una capa encima de la otra. El blanco de las partes es transparente.

Limitaciones: el resultado se ve "grisáceo" con el fondo ruidoso (es
inherente al método); el contraste es 50%. Cada parte es 2x más grande que
el original. NUNCA reutilices una parte con otro mensaje: igual que un
one-time pad, reutilizar la misma parte filtra información.
"""

import argparse
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Patrones 2x2 con exactamente 2 negros (1=negro). Seis posibilidades.
PATRONES = np.array([
    [[1, 0], [0, 1]], [[0, 1], [1, 0]],
    [[1, 1], [0, 0]], [[0, 0], [1, 1]],
    [[1, 0], [1, 0]], [[0, 1], [0, 1]],
], dtype=np.uint8)


def _indices_aleatorios(n: int) -> np.ndarray:
    """n enteros uniformes en [0,6) usando os.urandom (cripto-seguro, sin sesgo)."""
    out = np.empty(0, dtype=np.uint8)
    while len(out) < n:
        b = np.frombuffer(os.urandom(2 * (n - len(out)) + 16), dtype=np.uint8)
        out = np.concatenate([out, b[b < 252] % 6])  # 252 = 6*42, descarta el sesgo
    return out[:n]


def texto_a_bits(texto: str, alto: int = 120) -> np.ndarray:
    try:
        fuente = ImageFont.load_default(size=alto)
    except TypeError:  # Pillow viejo sin fuentes escalables
        fuente = ImageFont.load_default()
    lineas = texto.split("\\n") if "\\n" in texto else texto.split("\n")
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    cajas = [tmp.textbbox((0, 0), l or " ", font=fuente) for l in lineas]
    ancho = max(c[2] - c[0] for c in cajas) + 40
    alto_linea = max(c[3] - c[1] for c in cajas) + 20
    img = Image.new("L", (ancho, alto_linea * len(lineas) + 20), 255)
    d = ImageDraw.Draw(img)
    for i, (l, c) in enumerate(zip(lineas, cajas)):
        d.text((20 - c[0], 10 + i * alto_linea - c[1]), l, font=fuente, fill=0)
    return (np.array(img) < 128).astype(np.uint8)


def imagen_a_bits(ruta: str, ancho_max: int = 400) -> np.ndarray:
    img = Image.open(ruta).convert("L")
    if img.width > ancho_max:
        img = img.resize((ancho_max, round(img.height * ancho_max / img.width)))
    return (np.array(img) < 128).astype(np.uint8)


def dividir(secreto: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    h, w = secreto.shape
    p = PATRONES[_indices_aleatorios(h * w)].reshape(h, w, 2, 2)
    # Pixel blanco: mismo patrón en ambas partes (superpuestas -> 2 de 4 negros = gris)
    # Pixel negro: patrones complementarios (superpuestas -> 4 de 4 negros = negro)
    q = np.where(secreto[..., None, None] == 1, 1 - p, p)

    def expandir(x):
        return x.transpose(0, 2, 1, 3).reshape(h * 2, w * 2)

    return expandir(p), expandir(q)


def a_imagen_transparente(bits: np.ndarray) -> Image.Image:
    rgba = np.zeros((*bits.shape, 4), dtype=np.uint8)
    rgba[..., 3] = bits * 255  # negro opaco donde hay 1, transparente donde hay 0
    return Image.fromarray(rgba, "RGBA")


def cargar_parte(ruta: str) -> np.ndarray:
    img = Image.open(ruta)
    if img.mode == "RGBA":
        a = np.array(img)
        return ((a[..., 3] > 127) & (a[..., :3].mean(axis=2) < 128)).astype(np.uint8)
    return (np.array(img.convert("L")) < 128).astype(np.uint8)


def superponer(a: np.ndarray, b: np.ndarray, limpiar: bool = False) -> Image.Image:
    if a.shape != b.shape:
        raise ValueError("Las dos partes tienen tamaños distintos.")
    juntas = a | b
    if limpiar:
        # Truco digital (no se puede con acetatos): bloque 2x2 todo negro -> negro, si no -> blanco
        h, w = juntas.shape
        bloques = juntas[: h // 2 * 2, : w // 2 * 2].reshape(h // 2, 2, w // 2, 2).sum(axis=(1, 3))
        juntas = (bloques == 4).astype(np.uint8)
    return Image.fromarray(((1 - juntas) * 255).astype(np.uint8), "L")


def main():
    ap = argparse.ArgumentParser(description="Criptografía visual: dos ruidos que juntos revelan un mensaje.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dividir")
    g = d.add_mutually_exclusive_group(required=True)
    g.add_argument("--texto", help='usá "\\n" para varias líneas')
    g.add_argument("--imagen")
    d.add_argument("-o", "--prefijo", default="parte")
    d.add_argument("--tamano", type=int, default=120, help="alto de letra en px")
    s = sub.add_parser("superponer")
    s.add_argument("parte_a")
    s.add_argument("parte_b")
    s.add_argument("-o", "--salida", default="revelado.png")
    s.add_argument("--limpiar", action="store_true", help="quita el ruido gris (solo digital)")
    a = ap.parse_args()

    if a.cmd == "dividir":
        bits = texto_a_bits(a.texto, a.tamano) if a.texto else imagen_a_bits(a.imagen)
        pa, pb = dividir(bits)
        for sufijo, parte in (("A", pa), ("B", pb)):
            a_imagen_transparente(parte).save(f"{a.prefijo}_{sufijo}.png")
        print(f"🔀 Creadas {a.prefijo}_A.png y {a.prefijo}_B.png ({pa.shape[1]}x{pa.shape[0]} px).")
        print("   Cada una sola es ruido puro. Juntas, revelan el secreto.")
        return

    try:
        img = superponer(cargar_parte(a.parte_a), cargar_parte(a.parte_b), a.limpiar)
    except ValueError as e:
        raise SystemExit(f"❌ {e}")
    img.save(a.salida)
    print(f"👀 Superposición guardada en {a.salida}")


if __name__ == "__main__":
    main()

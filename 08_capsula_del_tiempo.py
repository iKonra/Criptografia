#!/usr/bin/env python3
"""
08 · CÁPSULA DEL TIEMPO CRIPTOGRÁFICA ⏳🔒
Un mensaje que NO SE PUEDE abrir antes de tiempo. No hay contraseña que
olvidar ni que robar: para abrirlo hay que hacer una cuenta larguísima que
no se puede paralelizar (ni con 1000 computadoras va más rápido).

Es el "puzzle de bloqueo temporal" de Rivest, Shamir y Wagner (1996):
calcular  2^(2^T) mod N  exige T elevaciones al cuadrado UNA DETRÁS DE OTRA.
Quien crea la cápsula conoce los factores de N y hace un atajo instantáneo;
quien la abre no tiene más remedio que hacer el camino largo.

Ideas: la respuesta del acertijo que se abre en 1 hora, el regalo digital
que no se puede espiar antes del cumple, un "no me dejes leer esto hasta
que se me pase el enojo", apuestas entre amigos.

Ejemplos:
  python 08_capsula_del_tiempo.py calibrar
  python 08_capsula_del_tiempo.py enterrar "Sí, me comí tu alfajor" --minutos 30 -o capsula.json
  python 08_capsula_del_tiempo.py desenterrar capsula.json

Limitación honesta: el tiempo es "en una compu como la que calibró". Una
compu más rápida, o código en C/GMP en vez de Python, puede abrirla varias
veces antes (típicamente 2x a 10x). Elegí el tiempo con margen. Lo que SÍ
se garantiza: nadie la abre en segundos, y el progreso se guarda si cortás.
"""

import argparse
import hashlib
import json
import os
import sys
import time

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

BITS = 2048


def calibrar(segundos: float = 2.0) -> float:
    n = rsa.generate_private_key(65537, BITS).public_key().public_numbers().n
    x, cuenta, t0 = 3, 0, time.perf_counter()
    while time.perf_counter() - t0 < segundos:
        for _ in range(2000):
            x = x * x % n
        cuenta += 2000
    return cuenta / (time.perf_counter() - t0)


def _clave(b: int) -> bytes:
    return hashlib.sha256(b.to_bytes((b.bit_length() + 7) // 8 or 1, "big")).digest()


def enterrar(mensaje: bytes, t: int) -> dict:
    priv = rsa.generate_private_key(65537, BITS).private_numbers()
    p, q = priv.p, priv.q
    n, phi = p * q, (p - 1) * (q - 1)
    a = 2
    # Atajo del creador: 2^(2^t) mod n = 2^(2^t mod phi) mod n  (Euler)
    b = pow(a, pow(2, t, phi), n)
    nonce = os.urandom(12)
    ct = AESGCM(_clave(b)).encrypt(nonce, mensaje, str(t).encode())
    return {"version": 1, "n": hex(n), "a": a, "t": t,
            "nonce": nonce.hex(), "cifrado": ct.hex(), "creada": int(time.time())}


def desenterrar(capsula: dict, progreso_cb=None, estado: dict | None = None) -> bytes:
    n, t = int(capsula["n"], 16), capsula["t"]
    estado = estado or {}
    x, i = estado.get("x", capsula["a"]), estado.get("i", 0)
    paso = 10_000
    while i < t:
        lote = min(paso, t - i)
        for _ in range(lote):
            x = x * x % n
        i += lote
        if progreso_cb:
            progreso_cb(i, t, x)
    try:
        return AESGCM(_clave(x)).decrypt(bytes.fromhex(capsula["nonce"]),
                                         bytes.fromhex(capsula["cifrado"]), str(t).encode())
    except InvalidTag:
        raise ValueError("La cápsula está corrupta o fue manipulada.") from None


def _fmt(seg: float) -> str:
    seg = int(seg)
    h, r = divmod(seg, 3600)
    m, s = divmod(r, 60)
    return f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s"


def main():
    ap = argparse.ArgumentParser(description="Mensajes que solo se pueden abrir después de un tiempo.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("calibrar")
    e = sub.add_parser("enterrar")
    e.add_argument("mensaje", nargs="?", help="si se omite, se lee de stdin")
    g = e.add_mutually_exclusive_group(required=True)
    g.add_argument("--minutos", type=float)
    g.add_argument("--horas", type=float)
    g.add_argument("--pasos", type=int, help="cantidad exacta de cuadrados (avanzado)")
    e.add_argument("--velocidad", type=float, help="cuadrados/segundo (si no, se calibra)")
    e.add_argument("-o", "--salida", default="capsula.json")
    d = sub.add_parser("desenterrar")
    d.add_argument("capsula")
    a = ap.parse_args()

    if a.cmd == "calibrar":
        print("⏱️  Midiendo velocidad de esta compu...")
        v = calibrar()
        print(f"   {v:,.0f} cuadrados/segundo -> 1 hora ≈ {int(v * 3600):,} pasos")
        return

    if a.cmd == "enterrar":
        msg = (a.mensaje if a.mensaje is not None else sys.stdin.read()).encode("utf-8")
        if a.pasos:
            t = a.pasos
        else:
            v = a.velocidad or (print("⏱️  Calibrando...", file=sys.stderr) or calibrar())
            seg = (a.minutos or 0) * 60 + (a.horas or 0) * 3600
            t = max(1, int(v * seg))
        cap = enterrar(msg, t)
        with open(a.salida, "w") as fh:
            json.dump(cap, fh, indent=1)
        print(f"⚰️  Cápsula enterrada en {a.salida} ({t:,} pasos).")
        print("   Ni vos podés abrirla antes: el atajo ya se descartó.")
        return

    with open(a.capsula) as fh:
        cap = json.load(fh)
    ruta_prog = a.capsula + ".progreso"
    estado = {}
    if os.path.exists(ruta_prog):
        with open(ruta_prog) as fh:
            estado = json.load(fh)
        estado["x"] = int(estado["x"], 16)
        print(f"↩️  Retomando desde el paso {estado['i']:,}")
    t0, i0, ultimo = time.time(), estado.get("i", 0), [0.0]

    def progreso(i, t, x):
        ahora = time.time()
        if ahora - ultimo[0] < 1 and i < t:
            return
        ultimo[0] = ahora
        vel = (i - i0) / max(ahora - t0, 1e-9)
        restante = (t - i) / vel if vel else 0
        barra = "█" * int(30 * i / t) + "░" * (30 - int(30 * i / t))
        print(f"\r⛏️  [{barra}] {100 * i / t:5.1f}%  faltan ~{_fmt(restante)}   ", end="", flush=True)
        with open(ruta_prog, "w") as fh:  # se puede cortar con Ctrl+C y retomar
            json.dump({"i": i, "x": hex(x)}, fh)

    try:
        msg = desenterrar(cap, progreso, estado)
    except KeyboardInterrupt:
        print("\n⏸️  Pausado. Volvé a correr el mismo comando para seguir.")
        return
    except ValueError as err:
        raise SystemExit(f"\n❌ {err}")
    if os.path.exists(ruta_prog):
        os.remove(ruta_prog)
    print("\n\n🎉 ¡Cápsula abierta!\n")
    print(msg.decode("utf-8", "replace"))


if __name__ == "__main__":
    main()

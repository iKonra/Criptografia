#!/usr/bin/env python3
"""
07 · TESTAMENTO PIRATA (Esquema de Shamir) 🏴‍☠️🗺️
Partí un secreto en N fragmentos de forma que hagan falta K cualesquiera
para recuperarlo. Con K-1 fragmentos no se sabe NADA (ni un bit) del
secreto: no es "faltan pedazos del rompecabezas", es seguridad matemática.

Usos reales (de verdad se usa así):
  - La frase semilla de tu billetera cripto: 5 fragmentos, 3 necesarios.
    Uno en tu casa, uno con tu vieja, uno en el banco... Si perdés 2, la
    recuperás igual. Si te roban 2, el ladrón no tiene nada.
  - La contraseña maestra del gestor de contraseñas para tu familia.
  - "Mis hijos solo pueden abrir esto si se ponen de acuerdo 3 de 4". 😈

Ejemplos:
  python 07_testamento_pirata.py repartir "el tesoro está bajo la palmera" -k 3 -n 5
  python 07_testamento_pirata.py recuperar 3-1-a8f3... 3-4-91bc... 3-5-0e7d...
  python 07_testamento_pirata.py recuperar -f fragmentos.txt

Formato de cada fragmento:  K-X-HEX  (K=necesarios, X=número de fragmento).
Incluye un checksum: si mezclás fragmentos de secretos distintos o alguno
tiene un error de tipeo, te avisa en vez de devolver basura.

Limitación honesta: el checksum detecta errores, pero no protege contra
alguien que fabrique un fragmento falso a propósito sabiendo cómo funciona.
"""

import argparse
import hashlib
import secrets
import sys

# --- Aritmética en GF(2^8) (el mismo campo que usa AES) ---
_EXP = [0] * 512
_LOG = [0] * 256
_x = 1
for _i in range(255):
    _EXP[_i] = _x
    _LOG[_x] = _i
    _x ^= (_x << 1) ^ (0x11B if _x & 0x80 else 0)  # multiplicar por 3 (generador)
    _x &= 0xFF
for _i in range(255, 512):
    _EXP[_i] = _EXP[_i - 255]


def _mul(a: int, b: int) -> int:
    return 0 if a == 0 or b == 0 else _EXP[_LOG[a] + _LOG[b]]


def _div(a: int, b: int) -> int:
    if b == 0:
        raise ZeroDivisionError
    return 0 if a == 0 else _EXP[(_LOG[a] - _LOG[b]) % 255]


def _evaluar(coefs: list[int], x: int) -> int:
    y = 0
    for c in reversed(coefs):  # Horner
        y = _mul(y, x) ^ c
    return y


CHECK = 4  # bytes de SHA-256 agregados para detectar errores


def repartir(secreto: bytes, k: int, n: int) -> list[str]:
    if not 2 <= k <= n <= 255:
        raise ValueError("Tiene que cumplirse 2 <= K <= N <= 255.")
    datos = secreto + hashlib.sha256(secreto).digest()[:CHECK]
    fragmentos = [bytearray() for _ in range(n)]
    for byte in datos:
        coefs = [byte] + [secrets.randbelow(256) for _ in range(k - 1)]
        for i in range(n):
            fragmentos[i].append(_evaluar(coefs, i + 1))
    return [f"{k}-{i + 1}-{f.hex()}" for i, f in enumerate(fragmentos)]


def recuperar(fragmentos: list[str]) -> bytes:
    puntos = {}
    k_esperado = None
    for f in fragmentos:
        try:
            k, x, h = f.strip().split("-")
            k, x, datos = int(k), int(x), bytes.fromhex(h)
        except ValueError:
            raise ValueError(f"Fragmento mal formado: {f[:20]}...") from None
        if k_esperado not in (None, k):
            raise ValueError("Los fragmentos son de repartos distintos (K no coincide).")
        k_esperado = k
        puntos[x] = datos
    if len(puntos) < k_esperado:
        raise ValueError(f"Faltan fragmentos: hay {len(puntos)} distintos y se necesitan {k_esperado}.")
    xs = list(puntos)[:k_esperado]
    largos = {len(puntos[x]) for x in xs}
    if len(largos) != 1:
        raise ValueError("Los fragmentos tienen largos distintos (¿de secretos distintos?).")

    # Interpolación de Lagrange evaluada en x=0
    resultado = bytearray()
    for pos in range(largos.pop()):
        s = 0
        for xi in xs:
            num, den = 1, 1
            for xj in xs:
                if xj != xi:
                    num = _mul(num, xj)
                    den = _mul(den, xi ^ xj)
            s ^= _mul(puntos[xi][pos], _div(num, den))
        resultado.append(s)
    secreto, check = bytes(resultado[:-CHECK]), bytes(resultado[-CHECK:])
    if hashlib.sha256(secreto).digest()[:CHECK] != check:
        raise ValueError("El checksum no coincide: algún fragmento está mal o son de secretos distintos.")
    return secreto


def main():
    ap = argparse.ArgumentParser(description="Reparte un secreto en fragmentos (Shamir).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("repartir")
    r.add_argument("secreto", nargs="?", help="si se omite, se lee de stdin")
    r.add_argument("-k", type=int, required=True, help="fragmentos necesarios")
    r.add_argument("-n", type=int, required=True, help="fragmentos totales")
    r.add_argument("--nombres", help="nombres separados por coma, para etiquetar (ej: Ana,Beto,Caro)")
    c = sub.add_parser("recuperar")
    c.add_argument("fragmentos", nargs="*")
    c.add_argument("-f", "--archivo", help="archivo con un fragmento por línea")
    a = ap.parse_args()

    if a.cmd == "repartir":
        secreto = (a.secreto if a.secreto is not None else sys.stdin.read().rstrip("\n")).encode("utf-8")
        try:
            frags = repartir(secreto, a.k, a.n)
        except ValueError as e:
            raise SystemExit(f"❌ {e}")
        nombres = a.nombres.split(",") if a.nombres else []
        print(f"🏴‍☠️ Secreto repartido en {a.n} fragmentos. Hacen falta {a.k} para abrirlo.\n")
        for i, f in enumerate(frags):
            quien = nombres[i].strip() if i < len(nombres) else f"Pirata #{i + 1}"
            print(f"🗺️  {quien}:\n    {f}\n")
        print("Dale UN fragmento a cada persona. Nadie puede hacer nada solo.")
        return

    frags = list(a.fragmentos)
    if a.archivo:
        with open(a.archivo, encoding="utf-8") as fh:
            frags += [l.strip() for l in fh if l.strip() and not l.startswith("#")]
    try:
        print("💰 Secreto recuperado:\n")
        print(recuperar(frags).decode("utf-8", "replace"))
    except ValueError as e:
        raise SystemExit(f"❌ {e}")


if __name__ == "__main__":
    main()

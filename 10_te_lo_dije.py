#!/usr/bin/env python3
"""
10 · "TE LO DIJE" CRIPTOGRÁFICO 🔮📜
Demostrá que predijiste algo ANTES de que pase, sin revelar la predicción
hasta que quieras. Es un "esquema de compromiso" (commitment scheme):

  1. HOY: escribís tu predicción. El script te da un código (hash) corto.
     Publicás ese código donde quede fecha: un tweet, un grupo de WhatsApp,
     un mail a vos mismo. El código no revela nada de la predicción.
  2. DESPUÉS: revelás la predicción + un número secreto (sal). Cualquiera
     puede verificar que coincide con el código publicado aquella vez.

No podés hacer trampa: es computacionalmente imposible encontrar otra
predicción que dé el mismo código (SHA-256). Y nadie puede adivinar tu
predicción a partir del código, gracias a la sal aleatoria de 256 bits
(sin ella, alguien podría probar "gana Boca", "gana River"... hasta pegarle).

Ejemplos:
  python 10_te_lo_dije.py predecir "Mi hermano va a dejar el gimnasio antes de marzo"
      -> imprime el código para publicar y guarda la_profecia.json (¡NO lo compartas aún!)
  python 10_te_lo_dije.py revelar la_profecia.json
  python 10_te_lo_dije.py verificar <codigo> "<prediccion>" <sal>

La fecha la garantiza DÓNDE publicás el código, no este script. Elegí un
lugar donde no se pueda editar sin que se note.
"""

import argparse
import hashlib
import hmac
import json
import secrets
import time
import unicodedata

PREFIJO = "TLD1"


def _normalizar(texto: str) -> bytes:
    # NFC para que "é" escrita de dos formas distintas dé el mismo hash
    return unicodedata.normalize("NFC", texto.strip()).encode("utf-8")


def comprometer(prediccion: str, sal: str | None = None) -> tuple[str, str]:
    sal = sal or secrets.token_hex(32)
    h = hashlib.sha256(PREFIJO.encode() + bytes.fromhex(sal) + _normalizar(prediccion)).hexdigest()
    return f"{PREFIJO}-{h}", sal


def verificar(codigo: str, prediccion: str, sal: str) -> bool:
    try:
        esperado, _ = comprometer(prediccion, sal)
    except ValueError:
        return False
    return hmac.compare_digest(esperado, codigo.strip())


def main():
    ap = argparse.ArgumentParser(description="Probá que lo predijiste antes.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("predecir")
    p.add_argument("prediccion")
    p.add_argument("-o", "--salida", default="la_profecia.json")
    r = sub.add_parser("revelar")
    r.add_argument("archivo")
    v = sub.add_parser("verificar")
    v.add_argument("codigo")
    v.add_argument("prediccion")
    v.add_argument("sal")
    a = ap.parse_args()

    if a.cmd == "predecir":
        codigo, sal = comprometer(a.prediccion)
        with open(a.salida, "w", encoding="utf-8") as fh:
            json.dump({"codigo": codigo, "prediccion": a.prediccion, "sal": sal,
                       "fecha_local": time.strftime("%Y-%m-%d %H:%M:%S")}, fh, ensure_ascii=False, indent=1)
        print("🔮 Profecía sellada. Publicá ESTE código donde quede la fecha:\n")
        print(f"   {codigo}\n")
        print(f"🤐 Guardá {a.salida} en secreto hasta el día del 'te lo dije'.")
        print("   Si lo perdés, no podés demostrar nada (la sal es imposible de recuperar).")
        return

    if a.cmd == "revelar":
        with open(a.archivo, encoding="utf-8") as fh:
            d = json.load(fh)
        if not verificar(d["codigo"], d["prediccion"], d["sal"]):
            raise SystemExit("❌ El archivo fue modificado: la predicción ya no coincide con el código.")
        print("📢 ¡TE LO DIJE!\n")
        print(f"   Predicción: {d['prediccion']}")
        print(f"   Sal:        {d['sal']}")
        print(f"   Código:     {d['codigo']}\n")
        print("Para que lo verifiquen ellos mismos:")
        print(f'   python 10_te_lo_dije.py verificar {d["codigo"]} "{d["prediccion"]}" {d["sal"]}')
        return

    if verificar(a.codigo, a.prediccion, a.sal):
        print("✅ VERIFICADO. Esa predicción es exactamente la que se selló con ese código.")
        print("   Si el código se publicó en tal fecha, la predicción existía en esa fecha. 🔮")
    else:
        print("❌ NO coincide. O la predicción cambió (aunque sea una coma), o la sal es otra.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
09 · ROMPE-CIFRADOS CLÁSICOS 🔨📜
¿Tu amigo se cree hacker porque "cifra" con César o Vigenère? Este script
rompe sus mensajes en milisegundos SIN conocer la clave, usando análisis
de frecuencias del español (la E y la A aparecen muchísimo, la K casi nunca).

Moraleja educativa: los cifrados clásicos son un juguete. Para algo serio,
usá los otros scripts de esta carpeta (AES-GCM).

Ejemplos:
  python 09_rompe_cifrados.py cifrar-cesar "Ataquen al amanecer" -k 7
  python 09_rompe_cifrados.py cifrar-vigenere "Ataquen al amanecer" -k LIMON
  python 09_rompe_cifrados.py romper "Hahxbnu hs hthulnly"
  python 09_rompe_cifrados.py romper -f mensaje_raro.txt

Cómo rompe Vigenère: 1) prueba largos de clave de 1 a 20; 2) con un largo
L, cada L-ésima letra es un César, así que lo rompe por frecuencias; 3) refina
cada letra de la clave viendo qué pares de letras (bigramas) quedan más
"españoles"; 4) se queda con la clave que mejor explica el texto, penalizando
las claves largas (si no, siempre ganaría una clave larguísima).

Limitaciones: necesita texto suficiente. Con menos de ~20 letras (César)
o ~10 letras por carácter de clave (Vigenère) puede equivocarse. Trabaja
sobre las 26 letras A–Z: la Ñ y los acentos se normalizan (á->a) o se dejan
sin cifrar.
"""

import argparse
import math
import sys
import unicodedata

A = "abcdefghijklmnopqrstuvwxyz"
# Frecuencias del español (%), Ñ sumada a N y acentos a su vocal base
FREQ = dict(zip(A, [12.53, 1.42, 4.68, 5.86, 13.68, 0.69, 1.01, 0.70, 6.25, 0.44, 0.02,
                    4.97, 3.15, 7.02, 8.68, 2.51, 0.88, 6.87, 7.98, 4.63, 3.93, 0.90,
                    0.01, 0.22, 0.90, 0.52]))


def normalizar(texto: str) -> str:
    """Saca acentos (á->a, ü->u) pero conserva la ñ como tal."""
    out = []
    for ch in texto:
        if ch in "ñÑ":
            out.append(ch)
        else:
            out.append(unicodedata.normalize("NFD", ch)[0])
    return "".join(out)


def _desplazar(ch: str, k: int) -> str:
    if "a" <= ch <= "z":
        return chr((ord(ch) - 97 + k) % 26 + 97)
    if "A" <= ch <= "Z":
        return chr((ord(ch) - 65 + k) % 26 + 65)
    return ch


def cesar(texto: str, k: int) -> str:
    return "".join(_desplazar(c, k) for c in normalizar(texto))


def vigenere(texto: str, clave: str, descifrar: bool = False) -> str:
    ks = [ord(c) - 97 for c in normalizar(clave).lower() if c in A]
    if not ks:
        raise ValueError("La clave tiene que tener letras A-Z.")
    out, i = [], 0
    for c in normalizar(texto):
        if c.lower() in A:
            out.append(_desplazar(c, -ks[i % len(ks)] if descifrar else ks[i % len(ks)]))
            i += 1
        else:
            out.append(c)
    return "".join(out)


def letras(texto: str) -> str:
    return "".join(c for c in normalizar(texto).lower() if c in A)


def chi2(s: str) -> float:
    n = len(s) or 1
    return sum((s.count(l) - FREQ[l] / 100 * n) ** 2 / (FREQ[l] / 100 * n) for l in A)


def romper_cesar(texto: str) -> tuple[int, str]:
    s = letras(texto)
    mejor = min(range(26), key=lambda k: chi2(cesar(s, -k)))
    return mejor, cesar(texto, -mejor)


# Texto de muestra para aprender qué pares de letras son típicos del español.
CORPUS = """
En un lugar de la Mancha, de cuyo nombre no quiero acordarme, no ha mucho tiempo
que vivía un hidalgo de los de lanza en astillero, adarga antigua, rocín flaco y
galgo corredor. Una olla de algo más vaca que carnero, salpicón las más noches,
duelos y quebrantos los sábados, lentejas los viernes, algún palomino de añadidura
los domingos, consumían las tres partes de su hacienda. La ciudad despertaba
lentamente mientras los vecinos abrían las ventanas y el olor del café recién hecho
llenaba las calles. Los chicos corrían hacia la escuela con las mochilas a cuestas y
el panadero saludaba a todos desde la puerta de su negocio. Nadie sabía que aquel
día iba a ser distinto, porque en la plaza principal alguien había dejado una caja
cerrada con un mensaje cifrado que nadie podía entender. El comisario llamó a su
sobrina, que estudiaba matemática en la universidad, y ella se sentó en un banco con
un cuaderno y un lápiz para contar cuántas veces aparecía cada letra. Después de un
rato encontró que la letra más frecuente correspondía a la e, y que muchas palabras
cortas parecían ser artículos como el, la, los y las. Con paciencia fue reemplazando
símbolos hasta que el mensaje empezó a tener sentido y todos quedaron sorprendidos
cuando leyó en voz alta lo que decía. Hay que ver para creer, dijo el viejo del
quiosco, y se fue caminando despacio mientras se reía solo. Esta historia nos
enseña que los secretos escritos con métodos antiguos no resisten mucho tiempo frente
a una persona curiosa que tiene ganas de descubrir la verdad y que sabe contar.
"""


def _tabla_bigramas():
    s = letras(CORPUS)
    cuenta = [[0.5] * 26 for _ in range(26)]  # suavizado: ningún par es imposible
    for a, b in zip(s, s[1:]):
        cuenta[ord(a) - 97][ord(b) - 97] += 1
    totales = [sum(f) for f in cuenta]
    return [[math.log(cuenta[i][j] / totales[i]) for j in range(26)] for i in range(26)]


LOGP = _tabla_bigramas()


def puntaje_bigramas(nums: list[int]) -> float:
    """Log-probabilidad promedio por par de letras (más alto = más español)."""
    if len(nums) < 2:
        return -99.0
    return sum(LOGP[a][b] for a, b in zip(nums, nums[1:])) / (len(nums) - 1)


def _clave_para_largo(c: list[int], L: int) -> list[int]:
    n = len(c)
    F = [FREQ[l] for l in A]
    # 1) punto de partida: cada columna es un César, lo rompemos por frecuencias
    clave = []
    for i in range(L):
        cnt = [0] * 26
        for x in c[i::L]:
            cnt[x] += 1
        clave.append(max(range(26), key=lambda k: sum(F[j] * cnt[(j + k) % 26] for j in range(26))))
    # 2) refinamiento: cambiamos una letra de la clave por vez si mejora los bigramas
    for _ in range(6):
        cambio = False
        for i in range(L):
            def aporte(k):
                total = 0.0
                for j in range(i, n, L):
                    p = (c[j] - k) % 26
                    if j > 0:
                        total += LOGP[(c[j - 1] - clave[(j - 1) % L]) % 26][p]
                    if j + 1 < n:
                        total += LOGP[p][(c[j + 1] - clave[(j + 1) % L]) % 26]
                return total
            if L == 1:
                mejor = max(range(26), key=lambda k: puntaje_bigramas([(x - k) % 26 for x in c]))
            else:
                mejor = max(range(26), key=aporte)
            if mejor != clave[i]:
                clave[i], cambio = mejor, True
        if not cambio:
            break
    return clave


def romper_vigenere(texto: str, largo_max: int = 20) -> list[tuple[str, str, float]]:
    c = [ord(x) - 97 for x in letras(texto)[:3000]]
    if not c:
        raise ValueError("El texto no tiene letras.")
    resultados = {}
    for L in range(1, min(largo_max, max(1, len(c) // 3)) + 1):
        clave = _clave_para_largo(c, L)
        # ¿es una repetición de una clave más corta? (LIMONLIMON -> LIMON)
        for sub in range(1, L):
            if L % sub == 0 and clave == clave[:sub] * (L // sub):
                clave = clave[:sub]
                break
        texto_clave = "".join(A[k] for k in clave)
        plano = [(x - clave[i % len(clave)]) % 26 for i, x in enumerate(c)]
        # Una clave más larga siempre "encaja" un poquito mejor (sobreajuste),
        # así que cada letra de clave cuesta una penalización fija (estilo AIC).
        total = puntaje_bigramas(plano) * (len(c) - 1) - 3.0 * len(clave)
        resultados.setdefault(texto_clave, total)
    orden = sorted(resultados.items(), key=lambda kv: -kv[1])
    return [(k, vigenere(texto, k, descifrar=True), p) for k, p in orden]


def main():
    ap = argparse.ArgumentParser(description="Cifra y rompe César y Vigenère.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nombre in ("cifrar-cesar", "descifrar-cesar"):
        p = sub.add_parser(nombre)
        p.add_argument("texto")
        p.add_argument("-k", type=int, required=True)
    for nombre in ("cifrar-vigenere", "descifrar-vigenere"):
        p = sub.add_parser(nombre)
        p.add_argument("texto")
        p.add_argument("-k", required=True)
    r = sub.add_parser("romper")
    r.add_argument("texto", nargs="?")
    r.add_argument("-f", "--archivo")
    a = ap.parse_args()

    if a.cmd == "cifrar-cesar":
        print(cesar(a.texto, a.k)); return
    if a.cmd == "descifrar-cesar":
        print(cesar(a.texto, -a.k)); return
    if a.cmd in ("cifrar-vigenere", "descifrar-vigenere"):
        print(vigenere(a.texto, a.k, descifrar=a.cmd.startswith("des"))); return

    if a.archivo:
        with open(a.archivo, encoding="utf-8") as fh:
            texto = fh.read()
    else:
        texto = a.texto if a.texto is not None else sys.stdin.read()
    n = len(letras(texto))
    if n < 15:
        print(f"⚠️  Solo {n} letras: con tan poco texto el resultado es poco confiable.\n")

    try:
        vig = romper_vigenere(texto)
    except ValueError as e:
        raise SystemExit(f"❌ {e}")
    clave, plano, _ = vig[0]
    if len(clave) == 1:
        k = A.index(clave)
        print(f"🔓 Parece CÉSAR con desplazamiento {k} (ROT{k}):\n\n{plano}")
    else:
        print(f"🔓 Parece VIGENÈRE con clave '{clave.upper()}':\n\n{plano}")
    if len(vig) > 1:
        print("\nOtras claves candidatas (por si la primera no tiene sentido):")
        for c, p, _ in vig[1:3]:
            print(f"   {c.upper():<14} {p[:55]}...")

if __name__ == "__main__":
    main()

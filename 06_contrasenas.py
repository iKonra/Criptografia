#!/usr/bin/env python3
"""
06 · GENERADOR DE CONTRASEÑAS RIDÍCULAS (PERO FUERTES) 🦙🔑
Genera frases-contraseña absurdas en español, fáciles de recordar y con
entropía calculada de verdad:

    Pingüino Sarcástico Baila En Tokio Mientras Tostadora ...

Y evalúa contraseñas existentes: te dice cuánto tardaría en romperse y,
opcionalmente, si apareció en filtraciones reales (Have I Been Pwned) SIN
enviar tu contraseña: solo se mandan los primeros 5 caracteres de su hash
SHA-1 (k-anonimato), y la comparación se hace en tu compu.

Ejemplos:
  python 06_contrasenas.py generar                 # frase absurda, >= 70 bits
  python 06_contrasenas.py generar --bits 90 -n 5
  python 06_contrasenas.py generar --modo palabras --sep "-"
  python 06_contrasenas.py evaluar                 # la pide sin mostrarla
  python 06_contrasenas.py evaluar --hibp          # + consulta filtraciones

Sobre la "fuerza": la entropía de las frases generadas es exacta (sale de
contar opciones elegidas al azar con `secrets`). La evaluación de
contraseñas que inventaste vos es una ESTIMACIÓN aproximada: los humanos
somos predecibles y los crackers lo saben. Tomala como orientativa.
"""

import argparse
import getpass
import hashlib
import math
import re
import secrets
import string
import urllib.error
import urllib.request

SUSTANTIVOS = """pingüino tostadora dinosaurio calcetín zapallo mapache unicornio burrito
astronauta canguro pulpo robot carpincho chorizo flamenco abuelo cactus tiburón
murciélago empanada fantasma tractor dragón gnomo hipopótamo koala lagarto mono
ninja ornitorrinco pirata queso ratón sapo tomate vampiro yeti zombi alfajor
bombero cocodrilo detective elefante faraón gorila hámster iguana jabalí kiwi
lémur mago narval oso panda pato quirquincho rinoceronte salame tucán vikingo
wombat camello brócoli perezoso mate dulce choclo ñandú puercoespín caracol
bigote chupetín guisante payaso mariachi samurái sombrero tornillo trombón
violín bandoneón submarino helicóptero monopatín paraguas ventilador microondas
sillón inodoro lavarropas inflador sacacorchos martillo yogur fideo ravioles
pochoclo panqueque budín flan""".split()

ADJETIVOS = """sarcástico furioso dormido elegante confundido brillante peludo valiente
dramático ninja cósmico melancólico gigante diminuto bailarín filosófico
hambriento invisible radiactivo sospechoso tímido rebelde salvaje oxidado
pegajoso esponjoso crujiente misterioso legendario despeinado educado
millonario aburrido feliz veloz lento torpe glorioso vegano gruñón bromista
dorado plateado violeta turquesa fosforescente perfumado cuántico medieval
futurista prehistórico intergaláctico tropical polar volador nadador inquieto
paranoico romántico sabio loco ruidoso silencioso maldito bendito eléctrico
magnético mojado congelado tostado relleno picante amargo""".split()

VERBOS = """baila canta grita duerme cocina vuela nada corre salta medita negocia
programa estornuda suspira llora ríe conspira patina trepa escala pinta
escribe lee dibuja silba aplaude rapea surfea maneja navega teletransporta
hackea juega pelea sueña despega aterriza explota brilla tiembla flota cae
gira rueda rebota muerde abraza besa saluda espía persigue esquiva roba
devuelve inventa construye destruye repara vende compra alquila hornea
fríe licúa congela derrite""".split()

LUGARES = """Tokio Marte Bariloche Narnia Júpiter París Ushuaia Atlantis Neptuno
Mordor Roma Venecia Kioto Lima Cusco Quito Bogotá Montevideo Asunción
Santiago Rosario Mendoza Salta Córdoba Tandil Cancún Oaxaca Havana Madrid
Sevilla Lisboa Berlín Oslo Moscú Pekín Seúl Hanói Bangkok Delhi Cairo Nairobi
Sídney Tasmania Alaska Groenlandia Islandia Laponia Siberia Saturno Plutón
Andrómeda Gotham Hogwarts Springfield Valhalla Olimpo Babilonia Troya
Esparta Pompeya Titicaca Patagonia Amazonas Sahara Himalaya Antártida
Venus Mercurio Urano""".split()

CONECTORES = ["en", "cerca de", "debajo de", "arriba de", "lejos de", "rumbo a"]

COMUNES = {  # top de contraseñas filtradas (muestra chica, la API cubre el resto)
    "123456", "password", "123456789", "12345678", "12345", "qwerty", "1234567",
    "111111", "1234567890", "123123", "abc123", "000000", "iloveyou", "contraseña",
    "admin", "welcome", "monkey", "dragon", "football", "futbol", "boca", "river",
    "letmein", "sunshine", "princess", "master", "qwerty123", "1q2w3e4r", "654321",
    "superman", "batman", "pokemon", "starwars", "hola123", "teamo", "argentina",
}


def _uniq(lista):
    return list(dict.fromkeys(lista))


def frase_absurda(bits_objetivo: float) -> tuple[str, float]:
    """Construye 'Sustantivo Adjetivo Verbo conector Lugar' repetido hasta llegar a los bits."""
    categorias = [_uniq(SUSTANTIVOS), _uniq(ADJETIVOS), _uniq(VERBOS), CONECTORES, _uniq(LUGARES)]
    partes, bits, i = [], 0.0, 0
    while bits < bits_objetivo:
        cat = categorias[i % len(categorias)]
        palabra = secrets.choice(cat)
        partes.append(palabra if cat is CONECTORES else palabra.capitalize())
        bits += math.log2(len(cat))
        i += 1
    return " ".join(partes), bits


def frase_palabras(bits_objetivo: float, sep: str) -> tuple[str, float]:
    todas = _uniq([w.lower() for w in SUSTANTIVOS + ADJETIVOS + VERBOS + LUGARES])
    por_palabra = math.log2(len(todas))
    n = math.ceil(bits_objetivo / por_palabra)
    return sep.join(secrets.choice(todas) for _ in range(n)), n * por_palabra


def tiempo_legible(segundos: float) -> str:
    unidades = [("años", 31557600), ("días", 86400), ("horas", 3600), ("minutos", 60), ("segundos", 1)]
    if segundos < 1:
        return "instantáneo"
    edad_universo = 4.35e17
    if segundos > edad_universo * 1000:
        return f"{segundos / edad_universo:.1e} veces la edad del universo"
    for nombre, s in unidades:
        if segundos >= s:
            v = segundos / s
            return f"{v:,.0f} {nombre}" if v < 1e6 else f"{v:.1e} {nombre}"
    return "instantáneo"


def estimar_entropia(pwd: str) -> tuple[float, list[str]]:
    avisos = []
    if pwd.lower() in COMUNES:
        return 5.0, ["Está en el top de contraseñas más usadas del mundo. 💀"]
    pool = 0
    pool += 26 if re.search(r"[a-z]", pwd) else 0
    pool += 26 if re.search(r"[A-Z]", pwd) else 0
    pool += 10 if re.search(r"\d", pwd) else 0
    pool += 33 if re.search(r"[^\w\s]", pwd) else 0
    pool += 1 if " " in pwd else 0
    pool += 40 if re.search(r"[^\x00-\x7f]", pwd) else 0
    bits = len(pwd) * math.log2(max(pool, 2))

    # Penalizaciones por patrones típicos que los crackers prueban primero
    if re.search(r"(.)\1{2,}", pwd):
        bits *= 0.8; avisos.append("Tiene caracteres repetidos (aaa, 111).")
    secuencias = ["0123456789", "abcdefghijklmnopqrstuvwxyz", "qwertyuiop", "asdfghjkl", "zxcvbnm"]
    if any(s[i:i + 4] in pwd.lower() for s in secuencias for i in range(len(s) - 3)):
        bits *= 0.75; avisos.append("Tiene secuencias de teclado o abecedario (1234, qwer, abcd).")
    if re.search(r"(19|20)\d\d", pwd):
        bits -= 7; avisos.append("Parece contener un año: es lo primero que se prueba.")
    if re.fullmatch(r"[A-Z]?[a-z]+\d{1,4}[!.?]?", pwd):
        bits *= 0.6; avisos.append("Patrón clásico Palabra+números(+!): muy predecible.")
    base = pwd.lower().translate(str.maketrans("4310$5@7", "aeiosaat"))
    if any(c in base for c in COMUNES if len(c) >= 4):
        bits *= 0.6; avisos.append("Contiene una contraseña común (aunque cambies a->4, e->3...).")
    if len(pwd) < 12:
        avisos.append("Menos de 12 caracteres: hoy se considera corta.")
    return max(bits, 0.0), avisos


def consultar_hibp(pwd: str) -> int | None:
    sha1 = hashlib.sha1(pwd.encode("utf-8")).hexdigest().upper()
    prefijo, resto = sha1[:5], sha1[5:]
    req = urllib.request.Request(
        f"https://api.pwnedpasswords.com/range/{prefijo}",
        headers={"User-Agent": "criptografia-scripts", "Add-Padding": "true"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            for linea in r.read().decode().splitlines():
                h, _, n = linea.partition(":")
                if h == resto:
                    return int(n)
        return 0
    except (urllib.error.URLError, TimeoutError):
        return None


def mostrar_tiempos(bits: float):
    escenarios = [
        ("Online, con límite de intentos (100/hora)", 100 / 3600),
        ("Online sin límite (1.000/s)", 1e3),
        ("Offline, hash lento bcrypt/scrypt (10.000/s)", 1e4),
        ("Offline, hash rápido con GPUs (100.000 millones/s)", 1e11),
    ]
    for nombre, vel in escenarios:
        print(f"   {nombre:<52} {tiempo_legible(2 ** bits / 2 / vel)}")


def main():
    ap = argparse.ArgumentParser(description="Genera y evalúa contraseñas.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generar")
    g.add_argument("--bits", type=float, default=70, help="entropía mínima (default 70)")
    g.add_argument("-n", type=int, default=3, help="cuántas generar")
    g.add_argument("--modo", choices=["absurda", "palabras", "aleatoria"], default="absurda")
    g.add_argument("--sep", default=" ")
    e = sub.add_parser("evaluar")
    e.add_argument("--hibp", action="store_true", help="consultar Have I Been Pwned (k-anonimato)")
    e.add_argument("--clave", help="(inseguro: queda en el historial) contraseña a evaluar")
    a = ap.parse_args()

    if a.cmd == "generar":
        for _ in range(a.n):
            if a.modo == "absurda":
                frase, bits = frase_absurda(a.bits)
                if a.sep != " ":
                    frase = frase.replace(" ", a.sep)
            elif a.modo == "palabras":
                frase, bits = frase_palabras(a.bits, a.sep)
            else:
                alfabeto = string.ascii_letters + string.digits + "!@#$%&*?-_=+"
                n = math.ceil(a.bits / math.log2(len(alfabeto)))
                frase, bits = "".join(secrets.choice(alfabeto) for _ in range(n)), n * math.log2(len(alfabeto))
            print(f"🔑 {frase}\n   ({bits:.0f} bits de entropía real)\n")
        print("Tiempo para romper la última, en el peor escenario (GPUs, hash rápido):")
        print("   " + tiempo_legible(2 ** bits / 2 / 1e11))
        return

    pwd = a.clave or getpass.getpass("Contraseña a evaluar (no se muestra): ")
    bits, avisos = estimar_entropia(pwd)
    nivel = ("💀 Pésima" if bits < 28 else "😬 Débil" if bits < 45 else
             "🙂 Aceptable" if bits < 60 else "💪 Fuerte" if bits < 80 else "🏰 Fortaleza")
    print(f"\n{nivel}  (~{bits:.0f} bits estimados, {len(pwd)} caracteres)\n")
    print("Tiempo estimado para adivinarla (promedio):")
    mostrar_tiempos(bits)
    for av in avisos:
        print(f"   ⚠️  {av}")
    if a.hibp:
        n = consultar_hibp(pwd)
        if n is None:
            print("\n🌐 No pude consultar Have I Been Pwned (¿sin internet?).")
        elif n:
            print(f"\n🚨 Apareció {n:,} veces en filtraciones reales. NO la uses, cambiala ya.")
        else:
            print("\n✅ No aparece en filtraciones conocidas de Have I Been Pwned.")


if __name__ == "__main__":
    main()

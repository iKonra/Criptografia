"""Pruebas de ida y vuelta para los 10 scripts.  Correr:  python -m unittest -v"""

import importlib.util
import os
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from cripto_comun import ErrorDescifrado, cifrar, descifrar  # noqa: E402


def cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(RAIZ, nombre + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def foto_falsa(w=200, h=150):
    rng = np.random.default_rng(0)
    return Image.fromarray(rng.integers(0, 256, (h, w, 3), dtype=np.uint8), "RGB")


class TestComun(unittest.TestCase):
    def test_ida_vuelta_y_clave_mala(self):
        blob = cifrar(b"hola", "clave")
        self.assertEqual(descifrar(blob, "clave"), b"hola")
        with self.assertRaises(ErrorDescifrado):
            descifrar(blob, "otra")
        alterado = blob[:-1] + bytes([blob[-1] ^ 1])
        with self.assertRaises(ErrorDescifrado):
            descifrar(alterado, "clave")


class TestScripts(unittest.TestCase):
    def test_01_esteganografia(self):
        m = cargar("01_esteganografia")
        img = foto_falsa()
        for pwd, nombre in ((None, None), ("pw", "plan.pdf")):
            flags, payload = m.armar_payload("secreto ñandú 🐸".encode(), nombre, pwd)
            out = m.ocultar(img, flags, payload)
            diff = np.abs(np.array(out, int) - np.array(img, int)).max()
            self.assertLessEqual(diff, 1)  # imperceptible
            f2, datos = m.extraer(out)
            self.assertEqual(f2, flags)
            if pwd:
                datos = descifrar(datos, pwd)
            self.assertTrue(datos.endswith("secreto ñandú 🐸".encode()))
        with self.assertRaises(ValueError):
            m.extraer(img)

    def test_02_emojis(self):
        m = cargar("02_cifrado_emojis")
        b = cifrar("nos vemos".encode(), "x")
        s = m.bytes_a_emojis(b)
        self.assertEqual(m.emojis_a_bytes(" ".join(s)), b)
        self.assertEqual(descifrar(m.emojis_a_bytes(s), "x"), b"nos vemos")

    def test_03_texto_invisible(self):
        m = cargar("03_texto_invisible")
        t = m.ocultar("Che, ¿jugamos?", "el profe es un robot")
        self.assertEqual(m.limpiar(t), "Che, ¿jugamos?")
        self.assertEqual(m.revelar(t, lambda: None), "el profe es un robot")
        t2 = m.ocultar("Hola", "ultra", "pw")
        self.assertEqual(m.revelar(t2, lambda: "pw"), "ultra")
        self.assertTrue(m.detectar(t2))
        self.assertFalse(m.detectar("texto normal"))

    def test_04_archivo_a_arte(self):
        m = cargar("04_archivo_a_arte")
        datos = os.urandom(5000)
        with tempfile.TemporaryDirectory() as d:
            ruta = os.path.join(d, "a.png")
            m.archivo_a_imagen(datos, "x.bin", "pw").save(ruta)
            nombre, rec = m.imagen_a_archivo(Image.open(ruta), lambda: "pw")
        self.assertEqual((nombre, rec), ("x.bin", datos))

    def test_05_visual(self):
        m = cargar("05_criptografia_visual")
        bits = m.texto_a_bits("HOLA", 40)
        a, b = m.dividir(bits)
        # Cada parte tiene exactamente 2 de 4 negros por bloque (no revela nada)
        h, w = bits.shape
        bloques_a = a.reshape(h, 2, w, 2).sum(axis=(1, 3))
        self.assertTrue((bloques_a == 2).all())
        juntas = (a | b).reshape(h, 2, w, 2).sum(axis=(1, 3))
        self.assertTrue(((juntas == 4) == (bits == 1)).all())
        with tempfile.TemporaryDirectory() as d:
            pa, pb = os.path.join(d, "a.png"), os.path.join(d, "b.png")
            m.a_imagen_transparente(a).save(pa)
            m.a_imagen_transparente(b).save(pb)
            self.assertTrue((m.cargar_parte(pa) == a).all())

    def test_06_contrasenas(self):
        m = cargar("06_contrasenas")
        frase, bits = m.frase_absurda(70)
        self.assertGreaterEqual(bits, 70)
        self.assertLess(m.estimar_entropia("123456")[0], 10)
        self.assertLess(m.estimar_entropia("Boca2024!")[0], 45)
        self.assertGreater(m.estimar_entropia(frase)[0], 60)

    def test_07_shamir(self):
        m = cargar("07_testamento_pirata")
        s = "el tesoro está bajo la palmera 🌴".encode()
        frags = m.repartir(s, 3, 5)
        import itertools
        for combo in itertools.combinations(frags, 3):
            self.assertEqual(m.recuperar(list(combo)), s)
        with self.assertRaises(ValueError):
            m.recuperar(frags[:2])
        otro = m.repartir(s, 3, 5)
        with self.assertRaises(ValueError):
            m.recuperar([frags[0], frags[1], otro[2]])

    def test_08_capsula(self):
        m = cargar("08_capsula_del_tiempo")
        cap = m.enterrar(b"me comi tu alfajor", 5000)
        self.assertEqual(m.desenterrar(cap), b"me comi tu alfajor")
        # retomar a mitad de camino da el mismo resultado
        n, x = int(cap["n"], 16), cap["a"]
        for _ in range(1234):
            x = x * x % n
        self.assertEqual(m.desenterrar(cap, estado={"i": 1234, "x": x}), b"me comi tu alfajor")

    def test_09_rompe(self):
        m = cargar("09_rompe_cifrados")
        plano = ("La criptografía clásica es muy divertida pero se rompe con facilidad "
                 "cuando el mensaje es largo y el idioma tiene letras muy frecuentes como la e y la a")
        k, roto = m.romper_cesar(m.cesar(plano, 11))
        self.assertEqual(k, 11)
        self.assertEqual(roto, m.normalizar(plano))
        clave, roto_v, _ = m.romper_vigenere(m.vigenere(plano, "LIMON"))[0]
        self.assertEqual(clave, "limon")
        self.assertEqual(roto_v, m.normalizar(plano))

    def test_10_te_lo_dije(self):
        m = cargar("10_te_lo_dije")
        codigo, sal = m.comprometer("Va a llover el sábado")
        self.assertTrue(m.verificar(codigo, "Va a llover el sábado", sal))
        self.assertFalse(m.verificar(codigo, "Va a llover el domingo", sal))
        self.assertFalse(m.verificar(codigo, "Va a llover el sábado", "00" * 32))


if __name__ == "__main__":
    unittest.main()

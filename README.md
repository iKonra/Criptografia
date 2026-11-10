# 🔐 Criptografía útil (y graciosa) en Python

10 herramientas de línea de comandos. Las que cifran usan criptografía moderna de verdad
(**scrypt + AES-256-GCM**, ver `cripto_comun.py`), no juguetes. Las que son juguetes
(César/Vigenère) están para romperlos.

```bash
pip install -r requirements.txt
```

| # | Script | Qué hace | ¿Seguro de verdad? |
|---|--------|----------|--------------------|
| 01 | `01_esteganografia.py` | Esconde un mensaje o un **archivo entero dentro de una foto**. La foto se ve igual. | Oculta + cifra (con `--cifrar`). Detectable por steganálisis. |
| 02 | `02_cifrado_emojis.py` | Cifra mensajes como **sopa de emojis** 😂🐸🍕 para pegar en el chat. | Sí (AES-GCM). `--sin-clave` es solo codificación. |
| 03 | `03_texto_invisible.py` | **Tinta invisible**: mete un secreto dentro de un texto normal con caracteres de ancho cero. También **detecta y limpia** textos marcados. | Oculta + cifra (con `--cifrar`). |
| 04 | `04_archivo_a_arte.py` | Convierte cualquier archivo (PDF, ZIP…) en una **imagen de "arte abstracto"** y viceversa. | Sí (AES-GCM). |
| 05 | `05_criptografia_visual.py` | Parte un mensaje en **dos imágenes de ruido**; superpuestas (en acetato) lo revelan. Se descifra con el ojo. | Sí, perfecto (one-time pad), si no reutilizás partes. |
| 06 | `06_contrasenas.py` | Genera **contraseñas absurdas y fuertes** ("Pingüino Sarcástico Baila En Tokio…") y evalúa las tuyas + chequeo en filtraciones (Have I Been Pwned, sin enviar tu contraseña). | Entropía exacta al generar; evaluación aproximada. |
| 07 | `07_testamento_pirata.py` | **Esquema de Shamir**: partí un secreto en N fragmentos y que hagan falta K para abrirlo. Ideal para frases semilla de billeteras cripto. | Sí (información perfecta con K-1 fragmentos). |
| 08 | `08_capsula_del_tiempo.py` | **Cápsula del tiempo**: un mensaje que no se puede abrir antes de X minutos/horas, ni con la "clave". | Sí, pero el tiempo depende del hardware del que abre. |
| 09 | `09_rompe_cifrados.py` | Cifra y **rompe César y Vigenère sin la clave** por análisis de frecuencias del español. | Educativo: demuestra que los cifrados clásicos no sirven. |
| 10 | `10_te_lo_dije.py` | **"Te lo dije" criptográfico**: sellá una predicción hoy, revelala después y que cualquiera verifique. | Sí (compromiso con SHA-256 + sal). |

## Ejemplos rápidos

```bash
# 01 · esconder un PDF dentro de la foto del gato
python 01_esteganografia.py ocultar gato.jpg gato.png -f plan.pdf --cifrar
python 01_esteganografia.py revelar gato.png

# 02 · emojis
python 02_cifrado_emojis.py cifrar "Nos vemos a las 9"

# 03 · tinta invisible
python 03_texto_invisible.py ocultar "Che, ¿mañana jugamos?" "el profe es un robot" > msg.txt
python 03_texto_invisible.py revelar < msg.txt
python 03_texto_invisible.py detectar < texto_sospechoso.txt

# 04 · tu tesis como cuadro
python 04_archivo_a_arte.py codificar tesis.pdf obra.png

# 05 · criptografía visual
python 05_criptografia_visual.py dividir --texto "TE AMO" -o carta
python 05_criptografia_visual.py superponer carta_A.png carta_B.png --limpiar

# 06 · contraseñas
python 06_contrasenas.py generar --bits 80
python 06_contrasenas.py evaluar --hibp

# 07 · Shamir
python 07_testamento_pirata.py repartir "mi frase semilla..." -k 3 -n 5 --nombres Ana,Beto,Caro,Dani,Eli
python 07_testamento_pirata.py recuperar 3-1-... 3-4-... 3-5-...

# 08 · cápsula del tiempo
python 08_capsula_del_tiempo.py enterrar "Sí, me comí tu alfajor" --minutos 30
python 08_capsula_del_tiempo.py desenterrar capsula.json   # Ctrl+C pausa, se retoma

# 09 · romper el "cifrado" de tu amigo
python 09_rompe_cifrados.py romper "Hahxbnu hs hthulnly"

# 10 · te lo dije
python 10_te_lo_dije.py predecir "Mi hermano deja el gimnasio antes de marzo"
python 10_te_lo_dije.py revelar la_profecia.json
```

Si no pasás `--clave`, la contraseña se pide sin mostrarse en pantalla (mejor: no queda en el historial de la terminal).

## Limitaciones que conviene saber

- **Imágenes (01, 04):** guardalas y mandalas siempre como **PNG original / archivo**. WhatsApp, Instagram,
  Google Fotos en modo ahorro, etc. recomprimen y destruyen el contenido.
- **Texto invisible (03):** algunas plataformas borran los caracteres de ancho cero.
- **Cápsula del tiempo (08):** el tiempo es "en una compu como la que calibró"; hardware más rápido o
  código optimizado en C puede abrirla varias veces antes. Usá margen.
- **Rompe-cifrados (09):** con textos cortos (menos de ~10 letras por letra de clave) puede fallar.
- **Te lo dije (10):** la fecha la prueba el lugar donde publicás el código, no el script.
- Nada de esto fue auditado por terceros. Para secretos con consecuencias reales (dinero, legales),
  usá herramientas establecidas (age, GPG, VeraCrypt, un gestor de contraseñas).

## Tests

```bash
python -m unittest discover -s tests -v
```

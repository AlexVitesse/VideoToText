# Video a Texto + Resumen IA

Aplicacion web que transcribe videos y genera resumenes inteligentes usando Google Speech Recognition y Gemini.

## Caracteristicas

- Transcripcion automatica de audio (gratuito con Google Speech Recognition)
- Generacion de resumenes estructurados con Gemini
- Soporte para videos largos (procesamiento en chunks)
- Exportacion a PDF con transcripcion y resumen
- Soporte multi-idioma (Espanol, Ingles, Portugues, Frances, Aleman)
- Interfaz web intuitiva con Streamlit

## Requisitos del Sistema

### FFmpeg (Obligatorio)

FFmpeg es necesario para extraer audio de los videos y para que pydub pueda procesar archivos de audio.

**Windows:**
1. Descarga FFmpeg desde https://ffmpeg.org/download.html
2. Extrae el archivo ZIP
3. Agrega la carpeta `bin` al PATH del sistema:
   - Busca "Variables de entorno" en Windows
   - Edita la variable `Path`
   - Agrega la ruta completa a la carpeta `bin` (ej: `C:\ffmpeg\bin`)
4. Reinicia la terminal y verifica con: `ffmpeg -version`

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

### Python

- Python 3.8 o superior

## Instalacion

1. **Clona o descarga el repositorio**

2. **Crea un entorno virtual (recomendado)**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **Instala las dependencias**
```bash
pip install -r requirements.txt
```

4. **Configura la API Key de Gemini**

Copia el archivo de ejemplo y agrega tu API key:
```bash
cp .env.example .env
```

Edita `.env` y reemplaza `tu_api_key_aqui` con tu API key real:
```
GEMINI_API_KEY=tu_api_key_real
```

### Obtener API Key de Gemini (Gratis)

1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Inicia sesion con tu cuenta de Google
3. Crea una nueva API Key
4. Copia la key y pegala en tu archivo `.env`

## Uso

### Aplicacion Web (Streamlit)

```bash
streamlit run app.py
```

Esto abrira la aplicacion en tu navegador (normalmente http://localhost:8501)

**Flujo de uso:**
1. Configura tu API Key de Gemini en el sidebar (si no usas .env)
2. Selecciona el idioma de transcripcion
3. Sube un archivo de video
4. Haz clic en "Procesar Video"
5. Espera a que se complete el proceso
6. Descarga los resultados (TXT o PDF)

### Version CLI (Solo conversion a audio)

Para convertir videos a MP3 en lote:

1. Crea una carpeta `videos_input` y coloca tus videos ahi
2. Ejecuta:
```bash
python converter_cli.py
```
3. Los archivos MP3 se guardaran en `mp3_output`

## Formatos Soportados

- **Video:** MP4, AVI, MOV, MKV, WEBM, FLV
- **Audio de salida:** MP3 (192 kbps, 44.1 kHz)

## Estructura del Proyecto

```
VideoToText/
├── app.py              # Aplicacion web Streamlit
├── converter_cli.py    # Version CLI para conversion en lote
├── requirements.txt    # Dependencias Python
├── .env.example        # Plantilla de variables de entorno
├── .gitignore          # Archivos ignorados por git
├── .streamlit/
│   └── config.toml     # Configuracion de Streamlit
└── README.md           # Este archivo
```

## Limites y Consideraciones

### Google Speech Recognition
- Gratuito con limite de aproximadamente 50 requests por dia
- Requiere conexion a internet
- Funciona mejor con audio claro y poco ruido de fondo

### Gemini
- El plan gratuito tiene un limite generoso de tokens
- Ideal para videos largos gracias a su ventana de contexto extendida
- Requiere conexion a internet

### Rendimiento
- Videos pequenos (< 100 MB): 1-2 minutos
- Videos medianos (100-500 MB): 2-5 minutos
- Videos grandes (> 500 MB): 5-15 minutos

El tiempo depende principalmente de la duracion del audio, no del tamano del archivo.

## Solucion de Problemas

### "FFmpeg no encontrado"
- Verifica que FFmpeg este instalado: `ffmpeg -version`
- Asegurate de que este en el PATH del sistema
- Reinicia la terminal despues de modificar el PATH

### "Error de transcripcion"
- Verifica tu conexion a internet
- El audio puede ser inaudible o tener mucho ruido
- Prueba con un archivo de audio mas corto

### "Error generando resumen"
- Verifica que tu API Key de Gemini sea valida
- Revisa que no hayas excedido el limite de tu plan

## Tecnologias Utilizadas

- [Streamlit](https://streamlit.io/) - Interfaz web
- [FFmpeg](https://ffmpeg.org/) - Procesamiento de video/audio
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) - Transcripcion de audio
- [pydub](https://github.com/jiaaro/pydub) - Manipulacion de audio
- [Google Gemini](https://ai.google.dev/) - Generacion de resumenes
- [FPDF2](https://py-pdf.github.io/fpdf2/) - Generacion de PDF

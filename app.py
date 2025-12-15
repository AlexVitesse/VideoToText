import streamlit as st
import subprocess
import os
import tempfile
import shutil
import time
import speech_recognition as sr
from pydub import AudioSegment
import google.generativeai as genai
from fpdf import FPDF
from dotenv import load_dotenv

load_dotenv()

# Configuracion de Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

def video_to_audio(video_path, audio_path):
    try:
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vn',
            '-acodec', 'libmp3lame',
            '-b:a', '192k',
            '-ar', '44100',
            audio_path,
            '-y'
        ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        output, _ = process.communicate()

        if process.returncode == 0:
            return True
        else:
            st.error(f"Error de FFmpeg: {output}")
            return False

    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False

def audio_to_wav(audio_path, wav_path):
    """Convierte audio a WAV para speech_recognition"""
    try:
        audio = AudioSegment.from_mp3(audio_path)
        audio = audio.set_channels(1)  # Mono
        audio = audio.set_frame_rate(16000)  # 16kHz
        audio.export(wav_path, format="wav")
        return True
    except Exception as e:
        st.error(f"Error convirtiendo a WAV: {str(e)}")
        return False

def transcribe_audio_chunks(wav_path, language="es-ES", progress_callback=None):
    """Transcribe audio en chunks para manejar archivos largos"""
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_wav(wav_path)

    # Dividir en chunks de 30 segundos
    chunk_length_ms = 30 * 1000
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

    full_transcript = []
    total_chunks = len(chunks)

    for i, chunk in enumerate(chunks):
        if progress_callback:
            progress_callback(i + 1, total_chunks)

        # Guardar chunk temporal
        chunk_path = wav_path.replace(".wav", f"_chunk_{i}.wav")
        chunk.export(chunk_path, format="wav")

        try:
            with sr.AudioFile(chunk_path) as source:
                audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data, language=language)
                    full_transcript.append(text)
                except sr.UnknownValueError:
                    full_transcript.append("[inaudible]")
                except sr.RequestError as e:
                    full_transcript.append(f"[error: {e}]")
        except Exception as e:
            full_transcript.append(f"[error procesando chunk: {e}]")
        finally:
            if os.path.exists(chunk_path):
                os.remove(chunk_path)

    return " ".join(full_transcript)

def generate_summary_with_gemini(transcript, api_key):
    """Genera un resumen usando Gemini"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""Analiza la siguiente transcripcion de un video y genera un resumen completo y estructurado.

El resumen debe incluir:
1. **Resumen Ejecutivo**: Un parrafo breve con los puntos principales
2. **Temas Principales**: Lista de los temas tratados
3. **Puntos Clave**: Los puntos mas importantes mencionados
4. **Conclusiones**: Las conclusiones o ideas finales del video

Transcripcion:
{transcript}

Por favor, genera el resumen en espanol y de forma clara y organizada."""

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generando resumen: {str(e)}"

def create_pdf(title, transcript, summary, output_path):
    """Crea un PDF con la transcripcion y el resumen"""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Pagina de titulo
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 60, "", ln=True)
    pdf.multi_cell(0, 10, title, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 20, "", ln=True)
    pdf.cell(0, 10, f"Generado el: {time.strftime('%Y-%m-%d %H:%M')}", align="C", ln=True)

    # Pagina de resumen
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "RESUMEN DEL VIDEO", ln=True)
    pdf.cell(0, 5, "", ln=True)
    pdf.set_font("Helvetica", "", 11)

    # Limpiar caracteres especiales para evitar errores
    summary_clean = summary.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, summary_clean)

    # Pagina de transcripcion
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "TRANSCRIPCION COMPLETA", ln=True)
    pdf.cell(0, 5, "", ln=True)
    pdf.set_font("Helvetica", "", 10)

    transcript_clean = transcript.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, transcript_clean)

    pdf.output(output_path)
    return True

def save_uploaded_file_chunked(uploaded_file, progress_placeholder=None):
    """Guarda el archivo en chunks con progreso"""
    try:
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, uploaded_file.name)

        uploaded_file.seek(0, 2)
        total_size = uploaded_file.tell()
        uploaded_file.seek(0)

        chunk_size = 1024 * 1024
        bytes_written = 0

        with open(file_path, 'wb') as f:
            while True:
                chunk = uploaded_file.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                bytes_written += len(chunk)

                if progress_placeholder and total_size > 0:
                    progress = int((bytes_written / total_size) * 100)
                    progress_placeholder.progress(min(progress, 99))

        return file_path, temp_dir
    except Exception as e:
        st.error(f"Error guardando archivo: {str(e)}")
        return None, None

def get_file_size_mb(file):
    """Obtiene el tamano del archivo en MB"""
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    return size / (1024 * 1024)

# Configuracion de la pagina
st.set_page_config(
    page_title="Video a Texto con Resumen IA",
    page_icon="🎬",
    layout="centered"
)

st.title("🎬 Video a Texto + Resumen IA")
st.markdown("### Transcribe videos y genera resumenes con Gemini")

# Sidebar para configuracion
with st.sidebar:
    st.header("⚙️ Configuracion")

    api_key = st.text_input(
        "API Key de Gemini",
        value=GEMINI_API_KEY,
        type="password",
        help="Obtén tu API key en https://makersuite.google.com/app/apikey"
    )

    st.markdown("---")
    st.markdown("### Opciones")
    generate_summary = st.checkbox("Generar resumen con IA", value=True)
    export_pdf = st.checkbox("Exportar a PDF", value=True)

    st.markdown("---")
    st.markdown("### Idioma de transcripcion")
    language = st.selectbox(
        "Selecciona el idioma",
        ["es-ES", "en-US", "pt-BR", "fr-FR", "de-DE"],
        index=0
    )

# Area principal
st.info("📊 Sube un video para transcribir y obtener un resumen inteligente")

uploaded_file = st.file_uploader(
    "Arrastra o selecciona un archivo de video",
    type=["mp4", "avi", "mov", "mkv", "webm", "flv"],
    help="Formatos soportados: MP4, AVI, MOV, MKV, WEBM, FLV"
)

if uploaded_file is not None:
    file_size = get_file_size_mb(uploaded_file)
    st.success(f"✅ Archivo cargado: **{uploaded_file.name}** ({file_size:.2f} MB)")

    if file_size > 500:
        st.warning("⚠️ Archivo grande. El proceso puede tardar varios minutos.")

    # Validar API key si se quiere resumen
    if generate_summary and not api_key:
        st.error("❌ Necesitas configurar tu API Key de Gemini en el sidebar para generar resumenes")
        st.stop()

    if st.button("🚀 Procesar Video", type="primary", use_container_width=True):

        status_container = st.container()

        with status_container:
            progress_bar = st.progress(0)
            status_text = st.empty()

            start_time = time.time()
            temp_dir = None

            try:
                # Fase 1: Guardar archivo
                status_text.markdown("### 📁 Fase 1/4: Guardando archivo...")
                video_path, temp_dir = save_uploaded_file_chunked(uploaded_file, progress_bar)

                if video_path is None:
                    st.error("❌ Error al guardar el archivo")
                    st.stop()

                progress_bar.progress(25)

                # Fase 2: Extraer audio
                status_text.markdown("### 🔊 Fase 2/4: Extrayendo audio...")
                audio_path = os.path.join(temp_dir, "audio.mp3")
                wav_path = os.path.join(temp_dir, "audio.wav")

                if not video_to_audio(video_path, audio_path):
                    st.error("❌ Error extrayendo audio")
                    st.stop()

                if not audio_to_wav(audio_path, wav_path):
                    st.error("❌ Error convirtiendo audio")
                    st.stop()

                progress_bar.progress(40)

                # Fase 3: Transcribir
                status_text.markdown("### 📝 Fase 3/4: Transcribiendo audio...")

                def update_transcription_progress(current, total):
                    progress = 40 + int((current / total) * 30)
                    progress_bar.progress(min(progress, 70))
                    status_text.markdown(f"### 📝 Transcribiendo... ({current}/{total} segmentos)")

                transcript = transcribe_audio_chunks(wav_path, language, update_transcription_progress)

                if not transcript or transcript.strip() == "":
                    st.error("❌ No se pudo obtener transcripcion")
                    st.stop()

                progress_bar.progress(70)

                # Fase 4: Generar resumen
                summary = ""
                if generate_summary:
                    status_text.markdown("### 🤖 Fase 4/4: Generando resumen con Gemini...")
                    summary = generate_summary_with_gemini(transcript, api_key)
                    progress_bar.progress(90)

                # Completado
                progress_bar.progress(100)
                total_time = time.time() - start_time
                status_text.markdown(f"### ✅ Proceso completado en {total_time:.1f} segundos")

                st.balloons()

                # Mostrar resultados
                st.markdown("---")

                # Tabs para organizar resultados
                tab1, tab2 = st.tabs(["📋 Resumen", "📝 Transcripcion"])

                with tab1:
                    if summary:
                        st.markdown(summary)
                    else:
                        st.info("No se genero resumen (opcion desactivada)")

                with tab2:
                    st.text_area("Transcripcion completa", transcript, height=400)

                # Descargas
                st.markdown("---")
                st.markdown("### 📥 Descargar resultados")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.download_button(
                        "📄 Transcripcion (.txt)",
                        transcript,
                        file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_transcripcion.txt",
                        mime="text/plain"
                    )

                with col2:
                    if summary:
                        st.download_button(
                            "📋 Resumen (.txt)",
                            summary,
                            file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_resumen.txt",
                            mime="text/plain"
                        )

                with col3:
                    if export_pdf:
                        pdf_path = os.path.join(temp_dir, "resultado.pdf")
                        title = uploaded_file.name.rsplit('.', 1)[0]

                        if create_pdf(title, transcript, summary or "Resumen no generado", pdf_path):
                            with open(pdf_path, "rb") as f:
                                st.download_button(
                                    "📕 Documento PDF",
                                    f.read(),
                                    file_name=f"{title}_completo.pdf",
                                    mime="application/pdf"
                                )

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                with st.expander("Ver detalles del error"):
                    st.code(traceback.format_exc())

            finally:
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass

# Informacion adicional
with st.expander("ℹ️ Informacion y Ayuda"):
    st.markdown("""
    ### Como funciona
    1. **Extraccion de audio**: Se extrae el audio del video usando FFmpeg
    2. **Transcripcion**: Se transcribe el audio usando Google Speech Recognition (gratuito)
    3. **Resumen IA**: Se genera un resumen estructurado usando Gemini
    4. **Exportacion**: Se genera un PDF con todo el contenido

    ### Requisitos
    - FFmpeg instalado en el sistema
    - API Key de Gemini (para resumenes)
    - Conexion a internet (para transcripcion y resumen)

    ### Obtener API Key de Gemini
    1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
    2. Crea una nueva API Key
    3. Pegala en el campo del sidebar

    ### Limites
    - Google Speech Recognition: ~50 requests/dia (gratuito)
    - Gemini: Depende de tu plan (el gratuito tiene limite generoso)
    """)

st.markdown("---")
st.markdown("🔧 **FFmpeg + Google Speech + Gemini** | 💻 **Procesamiento local**")

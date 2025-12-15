import streamlit as st
import subprocess
import os
import tempfile
import shutil
import time

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
        
        # Esperar a que termine
        output, _ = process.communicate()
        
        if process.returncode == 0:
            return True
        else:
            st.error(f"Error de FFmpeg: {output}")
            return False
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False

def save_uploaded_file_chunked(uploaded_file, progress_placeholder=None):
    """Guarda el archivo en chunks pequeños con progreso"""
    try:
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, uploaded_file.name)
        
        # Obtener tamaño total
        uploaded_file.seek(0, 2)
        total_size = uploaded_file.tell()
        uploaded_file.seek(0)
        
        # Guardar en chunks
        chunk_size = 1024 * 1024  # 1MB chunks
        bytes_written = 0
        
        with open(file_path, 'wb') as f:
            while True:
                chunk = uploaded_file.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                bytes_written += len(chunk)
                
                # Actualizar progreso
                if progress_placeholder and total_size > 0:
                    progress = int((bytes_written / total_size) * 100)
                    progress_placeholder.progress(min(progress, 99))
        
        return file_path, temp_dir
    except Exception as e:
        st.error(f"Error guardando archivo: {str(e)}")
        return None, None

def get_file_size_mb(file):
    """Obtiene el tamaño del archivo en MB"""
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    return size / (1024 * 1024)

# Configuración
st.set_page_config(
    page_title="Conversor Video a Audio",
    page_icon="🎵",
    layout="centered"
)

st.title("🎵 Conversor de Video a Audio")
st.markdown("### Convierte videos a audio MP3")

# Información
st.info("📊 Tamaño máximo: 5 GB | ⏱️ Ten paciencia con archivos grandes")

uploaded_file = st.file_uploader(
    "Arrastra o selecciona un archivo de video", 
    type=["mp4", "avi", "mov", "mkv", "webm", "flv"],
    help="Formatos soportados: MP4, AVI, MOV, MKV, WEBM, FLV"
)

if uploaded_file is not None:
    file_size = get_file_size_mb(uploaded_file)
    st.success(f"✅ Archivo cargado: **{file_size:.2f} MB**")
    
    # Advertencia para archivos muy grandes
    if file_size > 1000:  # Mayor a 1GB
        st.warning("⚠️ Archivo grande detectado. La carga y conversión pueden tardar varios minutos.")
    
    # Vista previa solo para archivos pequeños
    if file_size < 50:
        with st.expander("👁️ Vista previa del video"):
            st.video(uploaded_file)
    
    # Botón de conversión
    if st.button("🚀 Convertir a MP3", type="primary", use_container_width=True):
        
        # Contenedor para mensajes de estado
        status_container = st.container()
        
        with status_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            time_text = st.empty()
            
            start_time = time.time()
            
            try:
                # Fase 1: Guardar archivo
                status_text.markdown("### 📁 Fase 1/2: Guardando archivo...")
                time_text.text("Esto puede tardar dependiendo del tamaño...")
                
                video_path, temp_dir = save_uploaded_file_chunked(
                    uploaded_file, 
                    progress_bar
                )
                
                if video_path is None:
                    st.error("❌ Error al guardar el archivo")
                    st.stop()
                
                elapsed = time.time() - start_time
                status_text.markdown(f"✅ Archivo guardado en {elapsed:.1f} segundos")
                time.sleep(1)
                
                # Fase 2: Convertir
                status_text.markdown("### 🔄 Fase 2/2: Convirtiendo a MP3...")
                time_text.text("Extrayendo audio del video...")
                progress_bar.progress(0)
                
                audio_path = os.path.join(temp_dir, "audio_output.mp3")
                
                # Simular progreso durante conversión
                conversion_start = time.time()
                
                # Iniciar conversión en segundo plano
                import threading
                conversion_done = [False]
                conversion_success = [False]
                
                def convert():
                    conversion_success[0] = video_to_audio(video_path, audio_path)
                    conversion_done[0] = True
                
                thread = threading.Thread(target=convert)
                thread.start()
                
                # Mostrar progreso mientras convierte
                while not conversion_done[0]:
                    elapsed = time.time() - conversion_start
                    progress = min(int((elapsed / (file_size / 10)) * 100), 95)
                    progress_bar.progress(progress)
                    time_text.text(f"Procesando... {elapsed:.0f}s transcurridos")
                    time.sleep(0.5)
                
                thread.join()
                
                if conversion_success[0]:
                    progress_bar.progress(100)
                    total_time = time.time() - start_time
                    status_text.markdown(f"### ✅ ¡Conversión completa en {total_time:.1f} segundos!")
                    time_text.empty()
                    
                    if os.path.exists(audio_path):
                        audio_size = os.path.getsize(audio_path) / (1024 * 1024)
                        
                        st.success(f"🎵 **Audio generado:** {audio_size:.2f} MB")
                        
                        # Leer archivo de audio
                        with open(audio_path, "rb") as f:
                            audio_data = f.read()
                        
                        # Botón de descarga
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            st.download_button(
                                label="📥 Descargar MP3",
                                data=audio_data,
                                file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}.mp3",
                                mime="audio/mpeg",
                                use_container_width=True
                            )
                        
                        st.balloons()
                    else:
                        st.error("❌ No se pudo generar el archivo de audio")
                else:
                    status_text.markdown("### ❌ Error en la conversión")
                    time_text.empty()
                    
            except Exception as e:
                st.error(f"❌ Error inesperado: {str(e)}")
                import traceback
                with st.expander("Ver detalles del error"):
                    st.code(traceback.format_exc())
            
            finally:
                # Limpieza
                try:
                    if 'temp_dir' in locals() and os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                        st.info("🧹 Archivos temporales eliminados")
                except Exception as e:
                    st.warning(f"⚠️ Error limpiando archivos: {e}")

# Información adicional
with st.expander("ℹ️ Información y Consejos"):
    st.markdown("""
    ### 📋 Formatos Soportados
    - **Video:** MP4, AVI, MOV, MKV, WEBM, FLV
    - **Audio de salida:** MP3 (192 kbps, 44.1 kHz)
    
    ### ⏱️ Tiempos Estimados
    - **Archivos pequeños (< 100 MB):** 10-30 segundos
    - **Archivos medianos (100-500 MB):** 30-90 segundos
    - **Archivos grandes (500 MB - 2 GB):** 2-5 minutos
    - **Archivos muy grandes (> 2 GB):** 5-15 minutos
    
    ### 💡 Consejos
    - No cierres ni refresques la página durante la conversión
    - Para archivos > 2 GB, asegúrate de tener buena conexión
    - Si falla, intenta con un archivo más pequeño primero
    """)

st.markdown("---")
st.markdown("🔧 **Powered by FFmpeg** | 💻 **Procesamiento local**")
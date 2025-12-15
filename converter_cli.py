
import subprocess
import os
import glob

# --- Configuración ---
VIDEO_DIR = "videos_input"
AUDIO_DIR = "mp3_output"
SUPPORTED_EXTENSIONS = ["mp4", "avi", "mov", "mkv", "webm", "flv"]
# -------------------

def video_to_audio_cli(video_path, audio_path):
    """
    Convierte un archivo de video a audio MP3 usando FFmpeg.
    Muestra la salida del comando en la terminal.
    """
    print(f"\n[INFO] Iniciando conversión para: {os.path.basename(video_path)}")
    
    try:
        # Comando FFmpeg para extraer audio, optimizado para calidad/compatibilidad.
        command = [
            'ffmpeg',
            '-i', video_path,      # Archivo de entrada
            '-vn',                 # Descartar el video
            '-acodec', 'libmp3lame',# Usar el codificador MP3
            '-b:a', '192k',        # Bitrate de audio a 192 kbps
            '-ar', '44100',        # Frecuencia de muestreo a 44.1 kHz
            audio_path,            # Archivo de salida
            '-y'                   # Sobrescribir si el archivo de salida ya existe
        ]
        
        # Usamos subprocess.run para esperar a que el comando termine
        # y capturar la salida en tiempo real si es necesario (aunque aquí no lo hacemos).
        # El proceso se mostrará directamente en la consola.
        result = subprocess.run(
            command,
            check=True,  # Lanza una excepción si FFmpeg devuelve un error
            capture_output=True, # Captura stdout y stderr
            text=True # Decodifica stdout/stderr como texto
        )
        
        print(f"[ÉXITO] Audio guardado en: {audio_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        # Si FFmpeg falla, su salida de error estará en e.stderr
        print(f"[ERROR] Falló la conversión para: {os.path.basename(video_path)}")
        print(f"[ERROR] Salida de FFmpeg:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print("[ERROR CRÍTICO] `ffmpeg` no se encontró en el PATH del sistema.")
        print("Por favor, asegúrate de que FFmpeg esté instalado y accesible.")
        return False
    except Exception as e:
        print(f"[ERROR INESPERADO] Ocurrió un error: {str(e)}")
        return False

def main():
    """
    Función principal para ejecutar el proceso de conversión.
    """
    print("--- Script de Conversión de Video a Audio (CLI) ---")
    
    # 1. Asegurarse de que el directorio de salida exista
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    # 2. Encontrar todos los archivos de video en el directorio de entrada
    video_files = []
    for ext in SUPPORTED_EXTENSIONS:
        # Usamos glob para encontrar archivos con cada extensión soportada
        video_files.extend(glob.glob(os.path.join(VIDEO_DIR, f"*.{ext}")))
        
    if not video_files:
        print(f"\n[ADVERTENCIA] No se encontraron videos en la carpeta '{VIDEO_DIR}'.")
        print("Asegúrate de colocar tus archivos de video allí.")
        return
        
    print(f"\n[INFO] Se encontraron {len(video_files)} video(s) para procesar.")
    
    # 3. Procesar cada archivo de video
    success_count = 0
    fail_count = 0
    
    for video_path in video_files:
        # Construir el nombre del archivo de salida
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        audio_path = os.path.join(AUDIO_DIR, f"{base_name}.mp3")
        
        # Realizar la conversión
        if video_to_audio_cli(video_path, audio_path):
            success_count += 1
        else:
            fail_count += 1
            
    # 4. Resumen final
    print("\n--- Resumen de la Operación ---")
    print(f"Conversiones exitosas: {success_count}")
    print(f"Conversiones fallidas:  {fail_count}")
    print("---------------------------------")

if __name__ == "__main__":
    main()

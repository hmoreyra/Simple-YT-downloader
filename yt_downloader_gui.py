import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
import threading
import os
import sys
import json
import urllib.request
import webbrowser

# --- CONFIGURACIÓN DE ACTUALIZACIONES ---
GITHUB_REPO = "hmoreyra/Simple-YT-downloader"
CURRENT_VERSION = "v1.2.0"
# ----------------------------------------

def get_config_path():
    if os.name == 'nt':
        base_dir = os.getenv('APPDATA', os.path.expanduser('~'))
    else:
        base_dir = os.path.join(os.path.expanduser('~'), '.config')
    app_dir = os.path.join(base_dir, 'YTDownloaderGUI')
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)
    return os.path.join(app_dir, 'config.json')

def get_default_downloads_path():
    if os.name == 'nt':
        try:
            import winreg
            sub_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            downloads_guid = "{374DE290-123F-4565-9164-39C4925E467B}"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                location = winreg.QueryValueEx(key, downloads_guid)[0]
            if os.path.exists(location):
                return location
        except Exception:
            pass
        return os.path.join(os.environ.get('USERPROFILE', os.path.expanduser('~')), 'Downloads')
    else:
        downloads_es = os.path.join(os.path.expanduser('~'), 'Descargas')
        if os.path.exists(downloads_es):
            return downloads_es
        return os.path.join(os.path.expanduser('~'), 'Downloads')

def load_config():
    config_file = get_config_path()
    default_save_path = get_default_downloads_path()
    default_config = {'save_path': default_save_path, 'format': 'Audio (.mp3)', 'compress': False, 'compress_level': 'Medio (Equilibrado)', 'resolution': 'Máxima', 'quality': 'Alta'}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                save_dir = data.get('save_path', '')
                if not save_dir or not os.path.exists(save_dir):
                    save_dir = default_save_path
                return {
                    'save_path': save_dir,
                    'format': data.get('format', 'Audio (.mp3)'),
                    'compress': data.get('compress', False),
                    'compress_level': data.get('compress_level', 'Medio (Equilibrado)'),
                    'resolution': data.get('resolution', 'Máxima'),
                    'quality': data.get('quality', 'Alta')
                }
        except:
            pass
    return default_config

def save_config(path, format_choice, compress=False, compress_level="Medio (Equilibrado)", resolution="Máxima", quality="Alta"):
    config_file = get_config_path()
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({'save_path': path, 'format': format_choice, 'compress': compress, 'compress_level': compress_level, 'resolution': resolution, 'quality': quality}, f)
    except:
        pass

def get_ffmpeg_path():
    """Retorna la ruta temporal donde PyInstaller extrae ffmpeg si está empaquetado"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Comprobar si el archivo ffmpeg de Windows fue empaquetado
        if os.path.exists(os.path.join(sys._MEIPASS, 'ffmpeg.exe')):
            return sys._MEIPASS
    return None

def get_resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso (útil para cuando está empaquetado)"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def browse_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        path_var.set(folder_path)
        save_config(folder_path, format_var.get(), compress_var.get(), compress_level_var.get(), res_var.get(), quality_var.get())

def download_audio():
    url = url_var.get().strip()
    save_path = path_var.get().strip()

    if not url:
        messagebox.showerror("Error", "Por favor ingresa la URL del video.")
        return
    if not save_path:
        messagebox.showerror("Error", "Por favor selecciona la carpeta de destino.")
        return
        
    if not os.path.exists(save_path):
        messagebox.showerror("Error", "La ruta de destino no existe.")
        return

    # Guardar en config en caso de que lo haya escrito a mano
    save_config(save_path, format_var.get(), compress_var.get(), compress_level_var.get(), res_var.get(), quality_var.get())

    # Deshabilitar el botón durante la descarga
    download_btn.config(state=tk.DISABLED)
    status_var.set("Descargando...")

    def run_download():
        ffmpeg_loc = get_ffmpeg_path()
        selected_format = format_var.get()
        quality_choice = quality_var.get()
        
        if quality_choice == "Máxima":
            audio_format = 'bestaudio/best'
            mp3_q = '320'
            post_args = {}
        elif quality_choice == "Alta":
            audio_format = 'bestaudio/best'
            mp3_q = '192'
            post_args = {}
        elif quality_choice == "Media":
            audio_format = 'bestaudio/best'
            mp3_q = '128'
            post_args = {}
        elif quality_choice == "Baja":
            audio_format = 'worstaudio/bestaudio/worst'
            mp3_q = '64'
            post_args = {
                'ExtractAudio': ['-b:a', '64k'],
                'Merger': ['-c:a', 'aac', '-b:a', '64k']
            }
        else: # Mínima (32k Mono)
            audio_format = 'worstaudio/bestaudio/worst'
            mp3_q = '32'
            post_args = {
                'ExtractAudio': ['-ac', '1', '-ar', '22050', '-b:a', '32k'],
                'Merger': ['-c:a', 'aac', '-b:a', '32k', '-ac', '1', '-ar', '22050']
            }

        if "Audio" in selected_format:
            codec = 'mp3'
            if "opus" in selected_format.lower():
                codec = 'opus'
            elif "m4a" in selected_format.lower():
                codec = 'm4a'

            ydl_opts = {
                'format': audio_format,
                'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': codec,
                }],
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'geo_bypass': True,
                'source_address': '0.0.0.0',
                'concurrent_fragment_downloads': 5,
            }
            if codec == 'mp3':
                ydl_opts['postprocessors'][0]['preferredquality'] = mp3_q
        else: # MP4
            res_choice = res_var.get()
            if res_choice == "Máxima":
                format_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
            else:
                height = res_choice.replace('p', '')
                format_str = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'

            ydl_opts = {
                'format': format_str,
                'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'geo_bypass': True,
                'source_address': '0.0.0.0',
                'concurrent_fragment_downloads': 5,
            }
            if selected_format == "Video (.mp4)" and compress_var.get():
                level = compress_level_var.get()
                if "Ligero" in level:
                    crf, preset = '23', 'fast'
                elif "Fuerte" in level:
                    crf, preset = '32', 'slow'
                else:
                    crf, preset = '28', 'medium'
                
                if quality_choice == "Mínima (32k Mono)":
                    audio_bitrate = '32k'
                elif quality_choice == "Baja":
                    audio_bitrate = '64k'
                elif quality_choice == "Media":
                    audio_bitrate = '128k'
                elif quality_choice == "Alta":
                    audio_bitrate = '192k'
                else:
                    audio_bitrate = '320k'

                args_list = [
                    '-c:v', 'libx264',
                    '-crf', crf,
                    '-preset', preset,
                    '-c:a', 'aac',
                    '-b:a', audio_bitrate
                ]
                if quality_choice == "Mínima (32k Mono)":
                    args_list.extend(['-ac', '1', '-ar', '22050'])
                ydl_opts['postprocessor_args'] = args_list
            elif post_args:
                ydl_opts['postprocessor_args'] = post_args

        # Si el script se ejecuta como un archivo empaquetado .exe, le indicamos dónde está el ffmpeg incrustado
        if ffmpeg_loc:
            ydl_opts['ffmpeg_location'] = ffmpeg_loc # type: ignore

        def progress_hook(d):
            if d['status'] == 'downloading':
                try:
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    if total > 0:
                        percent = (downloaded / total) * 100
                        app.after(0, lambda p=percent: progress_bar.config(value=p))  # type: ignore
                        
                        speed = d.get('speed', 0)
                        if speed:
                            speed_mb = speed / 1024 / 1024
                            app.after(0, lambda p=percent, s=speed_mb: status_var.set(f"Descargando... {p:.1f}% ({s:.2f} MB/s)"))  # type: ignore
                        else:
                            app.after(0, lambda p=percent: status_var.set(f"Descargando... {p:.1f}%"))  # type: ignore
                except Exception:
                    pass
            elif d['status'] == 'finished':
                app.after(0, lambda: progress_bar.config(value=100))  # type: ignore
                app.after(0, lambda: status_var.set("Procesando archivo... (Esto puede tardar)"))  # type: ignore

        ydl_opts['progress_hooks'] = [progress_hook]  # type: ignore

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            # Llamar al hilo principal para actualizar la GUI
            app.after(0, on_download_complete, True)  # type: ignore
        except Exception as e:
            app.after(0, on_download_complete, False, str(e))  # type: ignore

    # Iniciar la descarga en un hilo separado para que no se congele la interfaz
    threading.Thread(target=run_download, daemon=True).start()

def on_download_complete(success, error_msg=""):
    download_btn.config(state=tk.NORMAL)
    progress_bar.config(value=0) # Reiniciar la barra de progreso
    if success:
        status_var.set("¡Descarga completa!")
        messagebox.showinfo("Éxito", f"El archivo se descargó correctamente en formato {format_var.get()}.")
        url_var.set("") # Limpiar la URL para la próxima descarga
    else:
        status_var.set("Error en la descarga")
        messagebox.showerror("Error", f"Hubo un problema al descargar:\n{error_msg}")

def check_for_updates():
    def run_check():
        status_var.set("Buscando actualizaciones...")
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 YTDownloader'})
            
            # Crear un contexto SSL sin verificación para evitar el error CERTIFICATE_VERIFY_FAILED 
            # al ejecutar el programa empaquetado (.exe) en Windows
            import ssl
            context = ssl._create_unverified_context()
            
            with urllib.request.urlopen(req, timeout=5, context=context) as response:
                data = json.loads(response.read().decode('utf-8'))
                latest_version = data.get('tag_name', '')
                
                if latest_version and latest_version != CURRENT_VERSION:
                    app.after(0, notify_update, latest_version, data.get('html_url'))  # type: ignore
                else:
                    app.after(0, show_updated_message)  # type: ignore
        except Exception as e:
            app.after(0, show_error_message, str(e))  # type: ignore
            
    threading.Thread(target=run_check, daemon=True).start()

def notify_update(version, url):
    status_var.set("Listo")
    respuesta = messagebox.askyesno("Actualización disponible", 
        f"¡Hay una nueva versión disponible ({version})!\nTu versión actual es {CURRENT_VERSION}.\n\n¿Deseas descargarla ahora en tu navegador?")
    if respuesta:
        webbrowser.open(url)

def show_updated_message():
    status_var.set("Listo")
    messagebox.showinfo("Actualizado", "Ya tienes la última versión instalada.")

def show_error_message(err):
    status_var.set("Listo")
    messagebox.showerror("Error", f"No se pudo conectar con GitHub.\n{err}")

# Configuración de la ventana principal
app = tk.Tk()
app.title(f"Descargador de YouTube ({CURRENT_VERSION})")
app.geometry("680x460")
app.minsize(680, 460)
app.resizable(True, True)

# Configurar icono si existe
icon_path = get_resource_path('logo.png')
if os.path.exists(icon_path):
    try:
        if sys.platform == 'win32':
            app.iconbitmap(get_resource_path('logo.ico'))
        elif sys.platform != 'linux':
            app.iconphoto(False, tk.PhotoImage(file=icon_path))
    except Exception:
        pass

# Cargar configuración
config_data = load_config()

# Variables
url_var = tk.StringVar()
path_var = tk.StringVar()
path_var.set(config_data['save_path'])
format_var = tk.StringVar()
format_var.set(config_data['format'])
compress_var = tk.BooleanVar(value=config_data.get('compress', False))
compress_level_var = tk.StringVar(value=config_data.get('compress_level', 'Medio (Equilibrado)'))
res_var = tk.StringVar(value=config_data.get('resolution', 'Máxima'))
quality_var = tk.StringVar(value=config_data.get('quality', 'Alta'))
status_var = tk.StringVar()
status_var.set("Listo")

def make_context_menu(widget):
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Copiar", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Pegar", command=lambda: widget.event_generate("<<Paste>>"))
    menu.add_command(label="Cortar", command=lambda: widget.event_generate("<<Cut>>"))
    
    def show_menu(event):
        menu.tk_popup(event.x_root, event.y_root)
        
    widget.bind("<Button-3>", show_menu)

# Frame principal para centrar y organizar los elementos
main_frame = tk.Frame(app, padx=30, pady=20)
main_frame.pack(fill=tk.BOTH, expand=True)

# Configurar la columna 1 para que se expanda dinámicamente
main_frame.columnconfigure(1, weight=1)

# Elementos de la UI
tk.Label(main_frame, text="URL del Video:").grid(row=0, column=0, padx=(0, 10), pady=15, sticky="e")
url_entry = tk.Entry(main_frame, textvariable=url_var)
url_entry.grid(row=0, column=1, pady=15, sticky="ew")
make_context_menu(url_entry)

tk.Label(main_frame, text="Carpeta:").grid(row=1, column=0, padx=(0, 10), pady=10, sticky="e")
entry_frame = tk.Frame(main_frame)
entry_frame.grid(row=1, column=1, pady=10, sticky="ew")
entry_frame.columnconfigure(0, weight=1)  # Hace que el entry de ruta ocupe el mayor espacio posible
path_entry = tk.Entry(entry_frame, textvariable=path_var)
path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
make_context_menu(path_entry)
tk.Button(entry_frame, text="Buscar", command=browse_folder).grid(row=0, column=1)

tk.Label(main_frame, text="Formato:").grid(row=2, column=0, padx=(0, 10), pady=10, sticky="e")

format_frame = tk.Frame(main_frame)
format_frame.grid(row=2, column=1, pady=10, sticky="w")

format_combo = ttk.Combobox(format_frame, textvariable=format_var, values=["Audio (.mp3)", "Audio (.opus)", "Audio (.m4a)", "Video (.mp4)"], state="readonly", width=15)
format_combo.pack(side=tk.LEFT)

tk.Label(format_frame, text="Res Máx:").pack(side=tk.LEFT, padx=(15, 5))
res_combo = ttk.Combobox(format_frame, textvariable=res_var, values=["Máxima", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"], state="readonly", width=10)
res_combo.pack(side=tk.LEFT)
res_combo.bind("<<ComboboxSelected>>", lambda e: save_config(path_var.get(), format_var.get(), compress_var.get(), compress_level_var.get(), res_var.get(), quality_var.get()))

tk.Label(format_frame, text="Calidad:").pack(side=tk.LEFT, padx=(15, 5))
quality_combo = ttk.Combobox(format_frame, textvariable=quality_var, values=["Máxima", "Alta", "Media", "Baja", "Mínima (32k Mono)"], state="readonly", width=14)
quality_combo.pack(side=tk.LEFT)
quality_combo.bind("<<ComboboxSelected>>", lambda e: save_config(path_var.get(), format_var.get(), compress_var.get(), compress_level_var.get(), res_var.get(), quality_var.get()))

compress_frame = tk.Frame(main_frame)
compress_frame.grid(row=3, column=1, sticky="w", pady=5)

def on_compress_toggle():
    if compress_var.get():
        compress_combo.config(state="readonly")
    else:
        compress_combo.config(state=tk.DISABLED)
    save_config(path_var.get(), format_var.get(), compress_var.get(), compress_level_var.get(), res_var.get(), quality_var.get())

compress_check = tk.Checkbutton(compress_frame, text="Reducir tamaño (Encode)", variable=compress_var, command=on_compress_toggle)
compress_check.pack(side=tk.LEFT)

compress_combo = ttk.Combobox(compress_frame, textvariable=compress_level_var, values=["Ligero (Alta Calidad)", "Medio (Equilibrado)", "Fuerte (Menor Tamaño)"], state="readonly", width=22)
compress_combo.pack(side=tk.LEFT, padx=5)
compress_combo.bind("<<ComboboxSelected>>", lambda e: save_config(path_var.get(), format_var.get(), compress_var.get(), compress_level_var.get(), res_var.get()))

def on_format_change(e):
    if format_var.get() == "Video (.mp4)":
        compress_check.config(state=tk.NORMAL)
        res_combo.config(state="readonly")
        on_compress_toggle()
    else:
        compress_check.config(state=tk.DISABLED)
        compress_combo.config(state=tk.DISABLED)
        res_combo.config(state=tk.DISABLED)
    save_config(path_var.get(), format_var.get(), compress_var.get(), compress_level_var.get(), res_var.get(), quality_var.get())

format_combo.bind("<<ComboboxSelected>>", on_format_change)
if format_var.get() != "Video (.mp4)":
    compress_check.config(state=tk.DISABLED)
    compress_combo.config(state=tk.DISABLED)
    res_combo.config(state=tk.DISABLED)
else:
    res_combo.config(state="readonly")
    on_compress_toggle()

download_btn = tk.Button(main_frame, text="Descargar", command=download_audio, bg="#4CAF50", fg="white", font=("Helvetica", 11, "bold"), cursor="hand2")
download_btn.grid(row=4, column=0, columnspan=2, pady=25, sticky="ew", ipady=8)

progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='determinate')
progress_bar.grid(row=5, column=0, columnspan=2, pady=(0, 10), sticky="ew")

tk.Label(main_frame, textvariable=status_var, fg="#555555").grid(row=6, column=0, columnspan=2, pady=5)

bottom_frame = tk.Frame(main_frame)
bottom_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=10)

bottom_frame.columnconfigure(0, weight=1)
bottom_frame.columnconfigure(1, weight=0)
bottom_frame.columnconfigure(2, weight=1)

update_btn = tk.Button(bottom_frame, text="Buscar Actualizaciones", command=check_for_updates, font=("Helvetica", 9), bg="#e0e0e0", cursor="hand2")
update_btn.grid(row=0, column=1)

def show_help():
    help_win = tk.Toplevel(app)
    help_win.title("Guía de Uso")
    help_win.geometry("900x500")
    help_win.minsize(900, 500)
    help_win.grab_set()
    
    text_widget = tk.Text(help_win, wrap=tk.WORD, font=("Helvetica", 10), padx=15, pady=15, bg="#f9f9f9")
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    scrollbar = ttk.Scrollbar(help_win, command=text_widget.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_widget.config(yscrollcommand=scrollbar.set)
    
    ayuda_texto = """Bienvenido al Descargador de YouTube

1. URL del Video:
Pega aquí el enlace de YouTube que quieres descargar.

2. Carpeta:
Elige dónde se guardará el archivo descargado.

3. Formatos (Extensiones):
• Audio (.mp3): Alta compatibilidad. Se puede reproducir en cualquier dispositivo, pero sufre una ligera pérdida de calidad por la conversión.
• Audio (.opus): La calidad original de YouTube. Excelente para audiófilos y pesa poco, pero algunos reproductores viejos no lo soportan.
• Audio (.m4a): Excelente calidad (AAC) sin reconversión. Ideal para dispositivos Apple (iPhone, Mac) y reproductores modernos.
• Video (.mp4): Descarga el video con audio incluido. Es el formato de video más compatible universalmente.

4. Resolución Máxima (Res Máx):
Te permite limitar la calidad del video. Si eliges "1080p" y el video original es 4K, se descargará en 1080p para ahorrar espacio y tiempo.

5. Calidad:
Controla la calidad del audio (tanto para formatos de solo audio como para la pista de audio de un video).
• Máxima: Descarga la mejor pista disponible sin importar el tamaño.
• Alta: Limita el audio a ~192kbps (Excelente balance).
• Media: Limita el audio a ~128kbps (Ocupa la mitad que la Máxima).
• Baja: Limita el audio a 64kbps o elige la peor pista para ahorrar espacio.
• Mínima (32k Mono): Comprime el audio a 32kbps Mono (22kHz, calidad radio AM). Reduce al máximo posible el peso del audio.

6. Reducir Tamaño (Encode):
Si marcas esta casilla, el programa recomprimirá el video usando FFmpeg para que ocupe menos espacio.
Opciones de Encode:
• Ligero (Alta Calidad): Comprime poco. Mantiene la mejor calidad visual.
• Medio (Equilibrado): El mejor balance entre reducción de tamaño y calidad visual.
• Fuerte (Menor Tamaño): Comprime al máximo. Ideal para enviar por WhatsApp o si tienes poco espacio, aunque puede verse un poco borroso."""
    
    text_widget.insert(tk.END, ayuda_texto)
    text_widget.config(state=tk.DISABLED)

help_btn = tk.Button(bottom_frame, text="Ayuda / Info", command=show_help, font=("Helvetica", 9), bg="#2196F3", fg="white", cursor="hand2")
help_btn.grid(row=0, column=2, sticky="e")

app.mainloop()

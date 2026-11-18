import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
import threading
import os
import sys
import json
import re
import ssl
import time
import urllib.request
import webbrowser

try:
    import certifi
except ImportError:
    certifi = None

# --- CONFIGURACIÓN DE ACTUALIZACIONES ---
GITHUB_REPO = "hmoreyra/Simple-YT-downloader"
CURRENT_VERSION = "v1.2.0"
# ----------------------------------------

ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

AUDIO_BITRATES = {
    "Máxima": "320k",
    "Alta": "192k",
    "Media": "128k",
    "Baja": "64k",
    "Mínima (32k Mono)": "32k",
}

THEMES = {
    "light": {
        "bg": "#f0f0f0",
        "surface": "#ffffff",
        "fg": "#1a1a1a",
        "muted_fg": "#555555",
        "btn_bg": "#e0e0e0",
        "btn_fg": "#1a1a1a",
        "btn_active_bg": "#d0d0d0",
        "accent_green": "#4CAF50",
        "accent_green_active": "#43A047",
        "accent_blue": "#2196F3",
        "accent_blue_active": "#1E88E5",
        "select_bg": "#cce8ff",
        "select_fg": "#000000",
        "check_select": "#ffffff",
        "help_bg": "#f9f9f9",
        "help_fg": "#1a1a1a",
        "combo_bg": "#e6e6e6",
        "combo_field": "#ffffff",
        "combo_disabled_fg": "#888888",
        "combo_disabled_bg": "#e8e8e8",
        "trough": "#dcdcdc",
        "progress": "#4CAF50",
    },
    "dark": {
        "bg": "#1e1e24",
        "surface": "#2b2b33",
        "fg": "#eaeaea",
        "muted_fg": "#a8a8b3",
        "btn_bg": "#34343e",
        "btn_fg": "#eaeaea",
        "btn_active_bg": "#444452",
        "accent_green": "#388E3C",
        "accent_green_active": "#2E7D32",
        "accent_blue": "#1976D2",
        "accent_blue_active": "#1565C0",
        "select_bg": "#264f78",
        "select_fg": "#ffffff",
        "check_select": "#2b2b33",
        "help_bg": "#25252d",
        "help_fg": "#e2e2e2",
        "combo_bg": "#34343e",
        "combo_field": "#2b2b33",
        "combo_disabled_fg": "#777784",
        "combo_disabled_bg": "#24242b",
        "trough": "#2b2b33",
        "progress": "#4CAF50",
    },
}


def strip_ansi(text):
    return ANSI_ESCAPE_RE.sub('', text)


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
    default_config = {
        'save_path': default_save_path,
        'format': 'Audio (.mp3)',
        'compress': False,
        'compress_level': 'Medio (Equilibrado)',
        'resolution': 'Máxima',
        'quality': 'Alta',
        'dark_mode': False,
    }
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
                    'compress': bool(data.get('compress', False)),
                    'compress_level': data.get('compress_level', 'Medio (Equilibrado)'),
                    'resolution': data.get('resolution', 'Máxima'),
                    'quality': data.get('quality', 'Alta'),
                    'dark_mode': bool(data.get('dark_mode', False)),
                }
        except Exception:
            pass
    return default_config


def save_config(
    path,
    format_choice,
    compress=False,
    compress_level="Medio (Equilibrado)",
    resolution="Máxima",
    quality="Alta",
    dark_mode=False,
):
    config_file = get_config_path()
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(
                {
                    'save_path': path,
                    'format': format_choice,
                    'compress': compress,
                    'compress_level': compress_level,
                    'resolution': resolution,
                    'quality': quality,
                    'dark_mode': dark_mode,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
    except Exception:
        pass


def save_current_config(*_args):
    save_config(
        path_var.get(),
        format_var.get(),
        compress_var.get(),
        compress_level_var.get(),
        res_var.get(),
        quality_var.get(),
        dark_mode_var.get(),
    )


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
        save_current_config()


def build_audio_post_args(codec, quality_choice):
    """Construye los argumentos de FFmpegExtractAudio respetando el codec elegido."""
    if quality_choice not in ("Baja", "Mínima (32k Mono)"):
        return {}

    encoder_map = {
        'mp3': 'libmp3lame',
        'opus': 'libopus',
        'm4a': 'aac',
    }
    encoder = encoder_map.get(codec, 'aac')
    if quality_choice == "Baja":
        return {'extractaudio': ['-c:a', encoder, '-b:a', '64k']}

    # Opus no admite 22050 Hz; usa 24000 Hz en su lugar
    sample_rate = '24000' if codec == 'opus' else '22050'
    return {'extractaudio': ['-c:a', encoder, '-ac', '1', '-ar', sample_rate, '-b:a', '32k']}


def download_audio():
    if str(download_btn['state']) == tk.DISABLED:
        return

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
    save_current_config()

    # Deshabilitar el botón durante la descarga
    download_btn.config(state=tk.DISABLED)
    status_var.set("Descargando...")

    selected_format = format_var.get()
    quality_choice = quality_var.get()
    res_choice = res_var.get()
    compress_enabled = compress_var.get()
    compress_level = compress_level_var.get()

    def run_download():
        ffmpeg_loc = get_ffmpeg_path()

        if quality_choice == "Máxima":
            audio_format = 'bestaudio/best'
            audio_q = '320'
        elif quality_choice == "Alta":
            audio_format = 'bestaudio/best'
            audio_q = '192'
        elif quality_choice == "Media":
            audio_format = 'bestaudio/best'
            audio_q = '128'
        elif quality_choice == "Baja":
            audio_format = 'worstaudio/bestaudio/worst'
            audio_q = '64'
        else:  # Mínima (32k Mono)
            audio_format = 'worstaudio/bestaudio/worst'
            audio_q = '32'

        common_opts = {
            'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'no_color': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'source_address': '0.0.0.0',
            'concurrent_fragment_downloads': 5,
        }

        if "Audio" in selected_format:
            codec = 'mp3'
            if "opus" in selected_format.lower():
                codec = 'opus'
            elif "m4a" in selected_format.lower():
                codec = 'm4a'

            pp_config = {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': codec,
            }
            if codec == 'mp3' or quality_choice != "Máxima":
                pp_config['preferredquality'] = audio_q

            ydl_opts = {
                **common_opts,
                'format': audio_format,
                'postprocessors': [pp_config],
            }
            post_args = build_audio_post_args(codec, quality_choice)
            if post_args:
                ydl_opts['postprocessor_args'] = post_args
        else:  # MP4
            if res_choice == "Máxima":
                format_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
            else:
                height = res_choice.replace('p', '')
                format_str = (
                    f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/'
                    f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'
                )

            ydl_opts = {
                **common_opts,
                'format': format_str,
                'merge_output_format': 'mp4',
            }

            if selected_format == "Video (.mp4)" and compress_enabled:
                if "Ligero" in compress_level:
                    crf, preset = '23', 'fast'
                elif "Fuerte" in compress_level:
                    crf, preset = '32', 'slow'
                else:
                    crf, preset = '28', 'medium'

                audio_bitrate = AUDIO_BITRATES.get(quality_choice, '192k')
                args_list = [
                    '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p',
                    '-crf', crf,
                    '-preset', preset,
                    '-c:a', 'aac',
                    '-b:a', audio_bitrate,
                    '-movflags', '+faststart',
                ]
                if quality_choice == "Mínima (32k Mono)":
                    args_list.extend(['-ac', '1', '-ar', '22050'])
                ydl_opts['postprocessor_args'] = {'merger': args_list}
            elif quality_choice == "Baja":
                ydl_opts['postprocessor_args'] = {'merger': ['-c:a', 'aac', '-b:a', '64k']}
            elif quality_choice == "Mínima (32k Mono)":
                ydl_opts['postprocessor_args'] = {
                    'merger': ['-c:a', 'aac', '-b:a', '32k', '-ac', '1', '-ar', '22050']
                }

        # Si el script se ejecuta como un archivo empaquetado .exe, le indicamos dónde está el ffmpeg incrustado
        if ffmpeg_loc:
            ydl_opts['ffmpeg_location'] = ffmpeg_loc  # type: ignore

        last_ui_update = 0.0

        def progress_hook(d):
            nonlocal last_ui_update
            status = d.get('status')
            if status == 'downloading':
                try:
                    now = time.monotonic()
                    if now - last_ui_update < 0.1:
                        return
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    downloaded = d.get('downloaded_bytes') or 0
                    if total > 0:
                        last_ui_update = now
                        percent = min(100.0, (downloaded / total) * 100)
                        speed = d.get('speed') or 0
                        if speed > 0:
                            speed_mb = speed / 1024 / 1024
                            msg = f"Descargando... {percent:.1f}% ({speed_mb:.2f} MB/s)"
                        else:
                            msg = f"Descargando... {percent:.1f}%"

                        def update_ui(p=percent, text=msg):
                            progress_bar.config(value=p)
                            status_var.set(text)

                        app.after(0, update_ui)  # type: ignore
                except Exception:
                    pass
            elif status == 'finished':
                last_ui_update = time.monotonic()

                def finish_ui():
                    progress_bar.config(value=100)
                    status_var.set("Procesando archivo... (Esto puede tardar)")

                app.after(0, finish_ui)  # type: ignore

        ydl_opts['progress_hooks'] = [progress_hook]  # type: ignore

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            # Llamar al hilo principal para actualizar la GUI
            app.after(0, on_download_complete, True)  # type: ignore
        except Exception as e:
            app.after(0, on_download_complete, False, strip_ansi(str(e)))  # type: ignore

    # Iniciar la descarga en un hilo separado para que no se congele la interfaz
    threading.Thread(target=run_download, daemon=True).start()


def on_download_complete(success, error_msg=""):
    download_btn.config(state=tk.NORMAL)
    progress_bar.config(value=0)  # Reiniciar la barra de progreso
    if success:
        status_var.set("¡Descarga completa!")
        messagebox.showinfo("Éxito", f"El archivo se descargó correctamente en formato {format_var.get()}.")
        url_var.set("")  # Limpiar la URL para la próxima descarga
    else:
        status_var.set("Error en la descarga")
        messagebox.showerror("Error", f"Hubo un problema al descargar:\n{error_msg}")


def check_for_updates():
    update_btn.config(state=tk.DISABLED)
    status_var.set("Buscando actualizaciones...")

    def run_check():
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 YTDownloader'})

            if certifi is not None:
                context = ssl.create_default_context(cafile=certifi.where())
            else:
                context = ssl.create_default_context()

            with urllib.request.urlopen(req, timeout=8, context=context) as response:
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
    update_btn.config(state=tk.NORMAL)
    status_var.set("Listo")
    respuesta = messagebox.askyesno(
        "Actualización disponible",
        f"¡Hay una nueva versión disponible ({version})!\nTu versión actual es {CURRENT_VERSION}.\n\n¿Deseas descargarla ahora en tu navegador?",
    )
    if respuesta and url:
        webbrowser.open(url)


def show_updated_message():
    update_btn.config(state=tk.NORMAL)
    status_var.set("Listo")
    messagebox.showinfo("Actualizado", "Ya tienes la última versión instalada.")


def show_error_message(err):
    update_btn.config(state=tk.NORMAL)
    status_var.set("Listo")
    messagebox.showerror("Error", f"No se pudo conectar con GitHub.\n{err}")


# Configuración de la ventana principal
app = tk.Tk()
app.title(f"Descargador de YouTube ({CURRENT_VERSION})")
app.geometry("680x460")
app.minsize(680, 460)
app.resizable(True, True)

style = ttk.Style(app)
if "clam" in style.theme_names():
    style.theme_use("clam")

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
path_var = tk.StringVar(value=config_data['save_path'])
format_var = tk.StringVar(value=config_data['format'])
compress_var = tk.BooleanVar(value=config_data.get('compress', False))
compress_level_var = tk.StringVar(value=config_data.get('compress_level', 'Medio (Equilibrado)'))
res_var = tk.StringVar(value=config_data.get('resolution', 'Máxima'))
quality_var = tk.StringVar(value=config_data.get('quality', 'Alta'))
dark_mode_var = tk.BooleanVar(value=config_data.get('dark_mode', False))
status_var = tk.StringVar(value="Listo")

context_menus = []
help_win_ref = None
help_text_ref = None


def make_context_menu(widget):
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Copiar", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Pegar", command=lambda: widget.event_generate("<<Paste>>"))
    menu.add_command(label="Cortar", command=lambda: widget.event_generate("<<Cut>>"))
    context_menus.append(menu)

    def show_menu(event):
        menu.tk_popup(event.x_root, event.y_root)

    widget.bind("<Button-3>", show_menu)


# Frame principal para centrar y organizar los elementos
main_frame = tk.Frame(app, padx=30, pady=20)
main_frame.pack(fill=tk.BOTH, expand=True)

# Configurar la columna 1 para que se expanda dinámicamente
main_frame.columnconfigure(1, weight=1)

# Elementos de la UI
url_label = tk.Label(main_frame, text="URL del Video:")
url_label.grid(row=0, column=0, padx=(0, 10), pady=15, sticky="e")
url_entry = tk.Entry(main_frame, textvariable=url_var)
url_entry.grid(row=0, column=1, pady=15, sticky="ew")
url_entry.bind("<Return>", lambda _e: download_audio())
make_context_menu(url_entry)

folder_label = tk.Label(main_frame, text="Carpeta:")
folder_label.grid(row=1, column=0, padx=(0, 10), pady=10, sticky="e")
entry_frame = tk.Frame(main_frame)
entry_frame.grid(row=1, column=1, pady=10, sticky="ew")
entry_frame.columnconfigure(0, weight=1)  # Hace que el entry de ruta ocupe el mayor espacio posible
path_entry = tk.Entry(entry_frame, textvariable=path_var)
path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
make_context_menu(path_entry)
browse_btn = tk.Button(entry_frame, text="Buscar", command=browse_folder, cursor="hand2")
browse_btn.grid(row=0, column=1)

format_label = tk.Label(main_frame, text="Formato:")
format_label.grid(row=2, column=0, padx=(0, 10), pady=10, sticky="e")

format_frame = tk.Frame(main_frame)
format_frame.grid(row=2, column=1, pady=10, sticky="w")

format_combo = ttk.Combobox(
    format_frame,
    textvariable=format_var,
    values=["Audio (.mp3)", "Audio (.opus)", "Audio (.m4a)", "Video (.mp4)"],
    state="readonly",
    width=15,
)
format_combo.pack(side=tk.LEFT)

res_label = tk.Label(format_frame, text="Res Máx:")
res_label.pack(side=tk.LEFT, padx=(15, 5))
res_combo = ttk.Combobox(
    format_frame,
    textvariable=res_var,
    values=["Máxima", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"],
    state="readonly",
    width=10,
)
res_combo.pack(side=tk.LEFT)
res_combo.bind("<<ComboboxSelected>>", save_current_config)

quality_label = tk.Label(format_frame, text="Calidad:")
quality_label.pack(side=tk.LEFT, padx=(15, 5))
quality_combo = ttk.Combobox(
    format_frame,
    textvariable=quality_var,
    values=["Máxima", "Alta", "Media", "Baja", "Mínima (32k Mono)"],
    state="readonly",
    width=14,
)
quality_combo.pack(side=tk.LEFT)
quality_combo.bind("<<ComboboxSelected>>", save_current_config)

compress_frame = tk.Frame(main_frame)
compress_frame.grid(row=3, column=1, sticky="w", pady=5)


def on_compress_toggle(save=True):
    if compress_var.get():
        compress_combo.config(state="readonly")
    else:
        compress_combo.config(state=tk.DISABLED)
    if save:
        save_current_config()


compress_check = tk.Checkbutton(
    compress_frame,
    text="Reducir tamaño (Encode)",
    variable=compress_var,
    command=on_compress_toggle,
)
compress_check.pack(side=tk.LEFT)

compress_combo = ttk.Combobox(
    compress_frame,
    textvariable=compress_level_var,
    values=["Ligero (Alta Calidad)", "Medio (Equilibrado)", "Fuerte (Menor Tamaño)"],
    state="readonly",
    width=22,
)
compress_combo.pack(side=tk.LEFT, padx=5)
compress_combo.bind("<<ComboboxSelected>>", save_current_config)


def on_format_change(_e=None):
    if format_var.get() == "Video (.mp4)":
        compress_check.config(state=tk.NORMAL)
        res_combo.config(state="readonly")
        on_compress_toggle(save=False)
    else:
        compress_check.config(state=tk.DISABLED)
        compress_combo.config(state=tk.DISABLED)
        res_combo.config(state=tk.DISABLED)
    save_current_config()


format_combo.bind("<<ComboboxSelected>>", on_format_change)
if format_var.get() != "Video (.mp4)":
    compress_check.config(state=tk.DISABLED)
    compress_combo.config(state=tk.DISABLED)
    res_combo.config(state=tk.DISABLED)
else:
    res_combo.config(state="readonly")
    on_compress_toggle(save=False)

download_btn = tk.Button(
    main_frame,
    text="Descargar",
    command=download_audio,
    bg="#4CAF50",
    fg="white",
    font=("Helvetica", 11, "bold"),
    cursor="hand2",
)
download_btn.grid(row=4, column=0, columnspan=2, pady=25, sticky="ew", ipady=8)

progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='determinate')
progress_bar.grid(row=5, column=0, columnspan=2, pady=(0, 10), sticky="ew")

status_label = tk.Label(main_frame, textvariable=status_var, fg="#555555")
status_label.grid(row=6, column=0, columnspan=2, pady=5)

bottom_frame = tk.Frame(main_frame)
bottom_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=10)

bottom_frame.columnconfigure(0, weight=1)
bottom_frame.columnconfigure(1, weight=0)
bottom_frame.columnconfigure(2, weight=1)


def apply_theme():
    theme_name = "dark" if dark_mode_var.get() else "light"
    c = THEMES[theme_name]

    app.configure(bg=c["bg"])
    for frame in (main_frame, entry_frame, format_frame, compress_frame, bottom_frame):
        frame.configure(bg=c["bg"])

    for lbl in (url_label, folder_label, format_label, res_label, quality_label):
        lbl.configure(bg=c["bg"], fg=c["fg"])
    status_label.configure(bg=c["bg"], fg=c["muted_fg"])

    for entry in (url_entry, path_entry):
        entry.configure(
            bg=c["surface"],
            fg=c["fg"],
            insertbackground=c["fg"],
            selectbackground=c["select_bg"],
            selectforeground=c["select_fg"],
        )

    for btn in (browse_btn, update_btn, theme_btn):
        btn.configure(
            bg=c["btn_bg"],
            fg=c["btn_fg"],
            activebackground=c["btn_active_bg"],
            activeforeground=c["btn_fg"],
        )

    download_btn.configure(
        bg=c["accent_green"],
        fg="white",
        activebackground=c["accent_green_active"],
        activeforeground="white",
    )
    help_btn.configure(
        bg=c["accent_blue"],
        fg="white",
        activebackground=c["accent_blue_active"],
        activeforeground="white",
    )

    compress_check.configure(
        bg=c["bg"],
        fg=c["fg"],
        activebackground=c["bg"],
        activeforeground=c["fg"],
        selectcolor=c["check_select"],
    )

    for menu in context_menus:
        menu.configure(
            bg=c["surface"],
            fg=c["fg"],
            activebackground=c["select_bg"],
            activeforeground=c["select_fg"],
        )

    style.configure(
        "TCombobox",
        fieldbackground=c["combo_field"],
        background=c["combo_bg"],
        foreground=c["fg"],
        arrowcolor=c["fg"],
        selectbackground=c["select_bg"],
        selectforeground=c["select_fg"],
    )
    style.map(
        "TCombobox",
        fieldbackground=[
            ("disabled", c["combo_disabled_bg"]),
            ("readonly", c["combo_field"]),
        ],
        foreground=[
            ("disabled", c["combo_disabled_fg"]),
            ("readonly", c["fg"]),
        ],
        background=[
            ("disabled", c["combo_disabled_bg"]),
            ("active", c["btn_active_bg"]),
        ],
        selectbackground=[("readonly", c["combo_field"])],
        selectforeground=[("readonly", c["fg"])],
    )
    app.option_add("*TCombobox*Listbox.background", c["surface"])
    app.option_add("*TCombobox*Listbox.foreground", c["fg"])
    app.option_add("*TCombobox*Listbox.selectBackground", c["select_bg"])
    app.option_add("*TCombobox*Listbox.selectForeground", c["select_fg"])

    style.configure(
        "Horizontal.TProgressbar",
        troughcolor=c["trough"],
        background=c["progress"],
        bordercolor=c["trough"],
        lightcolor=c["progress"],
        darkcolor=c["progress"],
    )
    style.configure(
        "Vertical.TScrollbar",
        background=c["btn_bg"],
        troughcolor=c["bg"],
        arrowcolor=c["fg"],
    )

    theme_btn.configure(text="Modo Claro" if dark_mode_var.get() else "Modo Oscuro")

    if help_win_ref is not None and help_win_ref.winfo_exists():
        help_win_ref.configure(bg=c["bg"])
        if help_text_ref is not None and help_text_ref.winfo_exists():
            help_text_ref.configure(
                bg=c["help_bg"],
                fg=c["help_fg"],
                insertbackground=c["help_fg"],
                selectbackground=c["select_bg"],
                selectforeground=c["select_fg"],
            )


def toggle_theme():
    dark_mode_var.set(not dark_mode_var.get())
    apply_theme()
    save_current_config()


theme_btn = tk.Button(bottom_frame, text="Modo Oscuro", command=toggle_theme, font=("Helvetica", 9), cursor="hand2")
theme_btn.grid(row=0, column=0, sticky="w")

update_btn = tk.Button(bottom_frame, text="Buscar Actualizaciones", command=check_for_updates, font=("Helvetica", 9), cursor="hand2")
update_btn.grid(row=0, column=1)


def show_help():
    global help_win_ref, help_text_ref
    if help_win_ref is not None and help_win_ref.winfo_exists():
        help_win_ref.focus_force()
        return

    c = THEMES["dark" if dark_mode_var.get() else "light"]
    help_win = tk.Toplevel(app)
    help_win.title("Guía de Uso")
    help_win.geometry("900x500")
    help_win.minsize(900, 500)
    help_win.configure(bg=c["bg"])
    help_win.grab_set()
    help_win_ref = help_win

    text_widget = tk.Text(
        help_win,
        wrap=tk.WORD,
        font=("Helvetica", 10),
        padx=15,
        pady=15,
        bg=c["help_bg"],
        fg=c["help_fg"],
        insertbackground=c["help_fg"],
        selectbackground=c["select_bg"],
        selectforeground=c["select_fg"],
        relief=tk.FLAT,
    )
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    help_text_ref = text_widget

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

apply_theme()

app.mainloop()

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
CURRENT_VERSION = "v1.0.0"
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
    default_config = {'save_path': default_save_path, 'format': 'MP3'}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                save_dir = data.get('save_path', '')
                if not save_dir or not os.path.exists(save_dir):
                    save_dir = default_save_path
                return {
                    'save_path': save_dir,
                    'format': data.get('format', 'MP3')
                }
        except:
            pass
    return default_config

def save_config(path, format_choice):
    config_file = get_config_path()
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({'save_path': path, 'format': format_choice}, f)
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
        save_config(folder_path, format_var.get())

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
    save_config(save_path, format_var.get())

    # Deshabilitar el botón durante la descarga
    download_btn.config(state=tk.DISABLED)
    status_var.set("Descargando...")

    def run_download():
        ffmpeg_loc = get_ffmpeg_path()
        selected_format = format_var.get()
        
        if selected_format == "MP3":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
            }
        else: # MP4
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'quiet': True,
                'no_warnings': True,
            }

        # Si el script se ejecuta como un archivo empaquetado .exe, le indicamos dónde está el ffmpeg incrustado
        if ffmpeg_loc:
            ydl_opts['ffmpeg_location'] = ffmpeg_loc # type: ignore

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
            with urllib.request.urlopen(req, timeout=5) as response:
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
app.geometry("520x300")
app.resizable(False, False)

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

# Elementos de la UI
tk.Label(app, text="URL del Video:").grid(row=0, column=0, padx=10, pady=15, sticky="w")
url_entry = tk.Entry(app, textvariable=url_var, width=45)
url_entry.grid(row=0, column=1, padx=10, pady=15, sticky="w")
make_context_menu(url_entry)

tk.Label(app, text="Carpeta:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
entry_frame = tk.Frame(app)
entry_frame.grid(row=1, column=1, padx=10, pady=5, sticky="w")
path_entry = tk.Entry(entry_frame, textvariable=path_var, width=33)
path_entry.pack(side=tk.LEFT, padx=(0, 5))
make_context_menu(path_entry)
tk.Button(entry_frame, text="Buscar", command=browse_folder).pack(side=tk.LEFT)

tk.Label(app, text="Formato:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
format_combo = ttk.Combobox(app, textvariable=format_var, values=["MP3", "MP4"], state="readonly", width=10)
format_combo.grid(row=2, column=1, padx=10, pady=5, sticky="w")
format_combo.bind("<<ComboboxSelected>>", lambda e: save_config(path_var.get(), format_var.get()))

download_btn = tk.Button(app, text="Descargar", command=download_audio, bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"), width=30)
download_btn.grid(row=3, column=0, columnspan=2, pady=15)

tk.Label(app, textvariable=status_var, fg="#555555").grid(row=4, column=0, columnspan=2)

update_btn = tk.Button(app, text="Buscar Actualizaciones", command=check_for_updates, font=("Helvetica", 8), bg="#e0e0e0")
update_btn.grid(row=5, column=0, columnspan=2, pady=5)

app.mainloop()

# Simple YT Downloader

Un descargador simple y ligero con interfaz gráfica para bajar videos y canciones (MP3/MP4) de YouTube. 
Está construido en Python utilizando **yt-dlp** para las descargas y **Tkinter** para la interfaz visual.

![Simple YT Downloader Logo](logo.png)

## Características principales 
- Descarga rápida de audio en formato **MP3** (con calidad de hasta 192kbps).
- Descarga de video en formato **MP4** con la mejor calidad disponible.
- Selección automática inteligente para la carpeta de descargas (por defecto tu carpeta nativa de "Descargas" o "Downloads").
- Botón incorporado para **buscar actualizaciones** directamente desde GitHub.
- Funcionalidad de copiar, pegar y cortar en las cajas de texto a través de un menú de clic derecho.
- Multiplataforma: Disponible para **Windows** y **Linux**.

## ¿Cómo descargarlo y utilizarlo?

¡No hace falta que instales nada raro ni que sepas de programación! Solo tenés que seguir estos pasos:

1. Dirígete a la sección de **[Releases](https://github.com/hmoreyra/Simple-YT-downloader/releases)** a la derecha de esta página (o haz clic en el botón "Releases").
2. En la versión más reciente (ej: `v1.0.0`), descarga el archivo correspondiente a tu sistema operativo:
   - Si usás Windows, descarga `yt_downloader_gui.exe`.
   - Si usás Linux, descarga `yt_downloader_gui` directamente.
3. Hacé doble clic sobre el archivo descargado para abrir el programa. ¡Eso es todo!
4. Pegá la URL de cualquier video de YouTube, elegí si querés solo el audio (MP3) o el video completo (MP4), y hacé clic en **Descargar**.

*(Aclaración para usuarios de Windows: el archivo descarga "ffmpeg.exe" incrustado en su interior, que es una herramienta necesaria para convertir la música, por lo que puede que tarde un par de segundos extra la primera vez que inicia en la PC).*

## Para desarrolladores

Si querés compilar tu propia versión o ver el código fuente:
1. Cloná o descargá este repositorio.
2. Asegurate de tener `python` instalado y crea un entorno virtual (recomendado).
3. Instalá las dependencias con `pip install yt-dlp pyinstaller`
4. Ejecutá la aplicación nativamente con `python yt_downloader_gui.py` o utilizá `pyinstaller` para empaquetarlo (ver la configuración detallada en el código fuente para los assets).

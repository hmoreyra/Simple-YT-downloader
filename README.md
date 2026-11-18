# Simple YT Downloader

Un descargador simple y ligero con interfaz gráfica para bajar videos y canciones de YouTube.
Está construido en Python utilizando **yt-dlp** para las descargas, **FFmpeg** para la conversión y **Tkinter** para la interfaz visual.

## Características principales
- Descarga de audio en formatos **MP3**, **Opus** y **M4A** con niveles de calidad configurables (desde Máxima hasta 32kbps Mono).
- Descarga de video en formato **MP4** con selector de resolución máxima (desde 144p hasta la máxima disponible) y opción de compresión (encode) para reducir el tamaño del archivo.
- **Modo oscuro** y **modo claro** con guardado automático de preferencias (carpeta, formato, calidad, resolución, compresión y tema).
- Selección automática de la carpeta nativa de "Descargas" o "Downloads".
- Botón para **buscar actualizaciones** desde GitHub y guía de uso integrada.
- Menú de clic derecho (copiar, pegar y cortar) en los campos de texto y soporte para iniciar la descarga con la tecla `Enter`.
- Multiplataforma: Disponible para **Windows** y **Linux**.

## ¿Cómo descargarlo y utilizarlo?

1. Dirigirse a la sección de **[Releases](https://github.com/hmoreyra/Simple-YT-downloader/releases)** a la derecha de esta página.
2. En la versión más reciente, descarga el archivo correspondiente a tu sistema operativo:
   - Si usás Windows, descarga `yt_downloader_gui.exe`.
   - Si usás Linux, descarga `yt_downloader_gui` directamente (requiere tener `ffmpeg` instalado en el sistema).
3. Hacé doble clic sobre el archivo descargado para abrir el programa.
4. Pegá la URL del video de YouTube, elegí el formato, resolución o calidad deseada, y hacé clic en **Descargar**.

*(Aclaración para usuarios de Windows: el ejecutable incluye `ffmpeg.exe` incrustado en su interior para realizar las conversiones, por lo que puede tardar un par de segundos extra al iniciar).*

## Para desarrolladores

Si querés compilar tu propia versión o ver el código fuente:
1. Cloná o descargá este repositorio.
2. Asegurate de tener `python` instalado y creá un entorno virtual (recomendado).
3. Instalá las dependencias con `pip install yt-dlp pyinstaller certifi`.
4. Ejecutá la aplicación nativamente con `python yt_downloader_gui.py` o utilizá `pyinstaller` para empaquetarla.

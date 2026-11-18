# Roadmap - Simple YT Downloader

Este documento recopila ideas y funcionalidades interesantes para implementar en futuras versiones de **Simple YT Downloader**.

---

## Descargas y Cola de Trabajo
- **Cola de descargas (Queue):** Permitir agregar múltiples URLs a una lista y procesarlas de forma secuencial o configurable en paralelo, mostrando el progreso individual y general.
- **Soporte completo de Playlists y Canales:** Detectar automáticamente cuando el enlace corresponde a una lista de reproducción, mostrar los videos contenidos y permitir seleccionar cuáles descargar (todos, un rango o selección manual).
- **Cancelar descarga en curso:** Agregar un botón para abortar limpiamente una descarga o conversión de FFmpeg que esté tardando demasiado, eliminando archivos temporales (`.part`).
- **Historial de descargas:** Guardar un registro local de los archivos descargados recientemente con acceso rápido para abrir el archivo o la carpeta contenedora.

## Metadatos, Subtítulos y Previsualización
- **Vista previa antes de descargar:** Al pegar una URL, consultar metadatos rápidos para mostrar el título, canal, duración y miniatura del video antes de iniciar la descarga.
- **Incrustación de carátulas y metadatos:** Añadir automáticamente la miniatura del video como portada (cover art) y etiquetas ID3 (título, artista, año) en archivos `.mp3` y `.m4a`.
- **Descarga de subtítulos:** Opción para descargar subtítulos disponibles (`.srt` / `.vtt`) en el idioma elegido o incrustarlos dentro del `.mp4`.

## Procesamiento Multimedia (FFmpeg)
- **Recorte por rango de tiempo:** Permitir especificar un tiempo de inicio y fin (`HH:MM:SS`) para descargar y extraer únicamente un fragmento del video o canción.
- **Aceleración por hardware al recomprimir:** Detectar GPU disponible (`NVENC`, `VAAPI`, `QSV`, `AMF`) para acelerar la opción *Reducir tamaño (Encode)* sin saturar la CPU.
- **Más formatos de salida:** Incorporar opciones como `.flac`, `.wav` para audio sin pérdida, y `.mkv` / `.webm` para video.
- **Normalización de volumen:** Opción para aplicar filtro `loudnorm` de FFmpeg y unificar el volumen entre distintas canciones descargadas.

## Experiencia de Usuario (UX) y Sistema
- **Pegado inteligente y Drag & Drop:** Botón rápido de *"Pegar URL"* junto al campo de texto y soporte para arrastrar enlaces directamente desde el navegador hacia la ventana.
- **Uso de cookies del navegador:** Integrar `--cookies-from-browser` (Chrome, Firefox, Edge) para poder descargar videos con restricción de edad, miembros o contenido privado del usuario.
- **Actualización de `yt-dlp` integrada / Auto-update:** Permitir actualizar el motor de descargas o descargar nuevas versiones desde GitHub directamente desde la app sin intervención manual.
- **Notificaciones del sistema:** Mostrar una notificación nativa del sistema operativo al finalizar descargas largas cuando la ventana está minimizada.
- **Soporte multi-idioma:** Selector de idioma (Español / Inglés).

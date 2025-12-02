🎙️ Audiolibro OCR IA (Streamlit + Tesseract + Edge-TTS)

Esta es una aplicación web personal construida con Python y Streamlit que permite convertir documentos PDF escaneados (imágenes) en audiolibros con voz neuronal de alta calidad.

Es ideal para estudiantes que necesitan convertir apuntes o libros en audio para estudiar en movimiento.

🛠️ Requisitos de Instalación (Configuración Local)

Para ejecutar esta aplicación en tu computadora, necesitas dos componentes principales: un motor OCR (Tesseract) y las librerías de Python.

Paso 1: Instalar el Motor OCR (Tesseract)

Tesseract es el "cerebro" que lee las imágenes de tu PDF. Este es un programa externo que debe instalarse en tu sistema operativo.

Descarga Directa: Descarga el instalador de 64 bits de Tesseract-OCR desde este enlace oficial:
tesseract-ocr-w64-setup-5.3.3.20231005.exe

Instalación: Ejecuta el archivo. Durante el proceso:

Llega a la pantalla "Choose Components" (Elegir Componentes).

Haz clic en el signo + al lado de "Additional Language Data".

Busca y marca la casilla "Spanish". (Esto es vital para leer las ñ y tildes).

Asegúrate de que la ruta de instalación sea la predeterminada: C:\Program Files\Tesseract-OCR

Paso 2: Instalar Librerías de Python

Abre la terminal de tu entorno Python (VS Code, etc.) y ejecuta el siguiente comando para instalar todas las dependencias necesarias:

pip install streamlit pymupdf pytesseract Pillow edge-tts


Paso 3: Configurar el Límite de Subida

Para evitar errores con PDFs grandes, Streamlit necesita un archivo de configuración.

Crea un nuevo archivo en la misma carpeta del proyecto llamado exactamente: config.toml

Pega el siguiente contenido dentro:

[server]
# Establece el límite de subida de archivos en 200MB, el máximo seguro para Streamlit.
maxUploadSize = 200


🚀 Uso de la Aplicación

Para iniciar la aplicación web en tu navegador:

Abre la terminal en la carpeta de tu proyecto.

Ejecuta el comando:

python -m streamlit run audiotext.py


El navegador se abrirá automáticamente con la interfaz.

Sube tu PDF.

En la barra lateral (⚙️ Configuración), ajusta las opciones:

🔄 Enderezar automáticamente: Recomendado para PDFs escaneados.

📖 Separar doble página: Útil para libros con dos páginas en una sola imagen.

Presiona "🎧 Convertir a Audio". El proceso de escaneo y generación de audio con IA comenzará y el MP3 aparecerá en la web para escuchar y descargar.

💡 Funcionamiento y Tecnología

Esta aplicación combina tecnologías avanzadas:

PyMuPDF (fitz): Extrae las páginas del PDF como imágenes.

Tesseract + PIL: Endereza (Auto-Rotación) y recorta las imágenes (Doble Página).

Edge-TTS: Convierte el texto extraído en una narración con voces neuronales (similar a los audios de ChatGPT o NotebookLM).

Módulo re: Limpia el texto para asegurar una lectura fluida, eliminando las pausas de "hipo" causadas por los saltos de línea del OCR.

## Despliegue en Streamlit Community Cloud

Para que la app funcione correctamente en Streamlit Cloud (incluyendo OCR y audio largo) añade los siguientes archivos al repositorio:

- `requirements.txt`: ya contiene las dependencias Python (fíjalas si necesitas reproducibilidad).
- `packages.txt`: listado de paquetes del sistema que Streamlit Cloud instalará con `apt` durante el build.

Contenido recomendado para `packages.txt`:

```
ffmpeg
tesseract-ocr
tesseract-ocr-spa
tesseract-ocr-eng
```

Con esto, Streamlit instalará `ffmpeg` y Tesseract (incluyendo datos para español e inglés) durante el despliegue, y las funciones de OCR y pydub funcionarán correctamente.

Pasos rápidos para deploy:

1. Sube el repo a GitHub (ya lo tienes en `main`).
2. Entra en https://streamlit.io/cloud y crea un nuevo deploy apuntando al repo y branch `main`.
3. Streamlit instalará `packages.txt` y `requirements.txt` automáticamente. Si la instalación falla, revisa los logs del deploy para ver el paquete que falta.

Si prefieres que lo configure yo (añadir `packages.txt`, fijar versiones y un breve README), ya lo hice y está commiteado en `main`.
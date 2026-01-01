# ocr_utils.py
import fitz  # PyMuPDF
import pytesseract
from pytesseract import Output
from PIL import Image
import io
import os
import re
import streamlit as st
from collections import Counter

# ================= CONFIGURACIÓN =================
def configurar_tesseract():
    """Configura Tesseract y devuelve True/False y la ruta/info."""
    try:
        if os.name == 'nt':
            # Intentar encontrar rutas comunes en Windows
            rutas = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
            ]
            for ruta in rutas:
                if os.path.exists(ruta):
                    pytesseract.pytesseract.tesseract_cmd = ruta
                    return True, ruta
        
        # Si ya está en PATH o en otros OS
        pytesseract.get_tesseract_version()
        return True, "Sistema / PATH"
    except Exception as e:
        return False, f"No encontrado. Error: {e}"

# ================= FUNCIONES DE PROCESAMIENTO =================
def limpiar_texto(texto):
    """Limpia texto para audio/procesamiento general."""
    if not texto:
        return ""
    texto = texto.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    texto = re.sub(r'\s+', ' ', texto)
    
    # Corregir palabras mal cortadas típicas de OCR
    correcciones = {
        r'(\w{2,3})-\s*(\w{3,})': r'\1\2',
        r'q u e': 'que',
        r'p a r a': 'para',
        r'c o n': 'con',
        r'(\w)\s+-\s+': r'\1', # Palabra cortada al final de línea
    }
    
    for patron, reemplazo in correcciones.items():
        texto = re.sub(patron, reemplazo, texto, flags=re.IGNORECASE)
    
    return texto.strip()

def corregir_orientacion(img):
    """Corrige la orientación de una imagen usando OSD."""
    try:
        datos = pytesseract.image_to_osd(img, output_type=Output.DICT)
        rotacion = datos["rotate"]
        if rotacion != 0:
            img = img.rotate(rotacion, expand=True)
            return img, True
    except:
        pass
    return img, False

def procesar_pagina_ocr(pagina, es_doble_pagina, auto_rotar):
    """Extrae texto de una página de PDF usando OCR."""
    try:
        # Renderizar la página con alta resolución (zoom 2)
        zoom_matrix = fitz.Matrix(2, 2)
        pix = pagina.get_pixmap(matrix=zoom_matrix)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        
        if auto_rotar:
            img, _ = corregir_orientacion(img)
        
        # Procesar como doble página si es necesario
        if es_doble_pagina:
            ancho, alto = img.size
            if ancho > alto: # Si el ancho es mayor que el alto, asumir doble página
                mitad = ancho // 2
                izquierda = img.crop((0, 0, mitad, alto))
                derecha = img.crop((mitad, 0, ancho, alto))
                texto_izq = pytesseract.image_to_string(izquierda, lang='spa+eng')
                texto_der = pytesseract.image_to_string(derecha, lang='spa+eng')
                return texto_izq + "\n\n" + texto_der
            
        return pytesseract.image_to_string(img, lang='spa+eng')
    except Exception as e:
        return f"[Error OCR en página: {str(e)[:100]}]"

def extraer_texto_pdf_ocr(archivo_pdf, es_doble_pagina=True, auto_rotar=True):
    """Extrae texto de PDF completo usando OCR con barra de progreso de Streamlit."""
    texto_total = []
    archivo_pdf.seek(0)
    
    try:
        doc = fitz.open(stream=archivo_pdf.read(), filetype="pdf")
        total_paginas = len(doc)
        
        barra = st.progress(0, "Iniciando OCR...")
        
        for i in range(total_paginas):
            pagina = doc.load_page(i)
            texto_pagina = procesar_pagina_ocr(pagina, es_doble_pagina, auto_rotar)
            texto_total.append(texto_pagina)
            
            progreso = (i + 1) / total_paginas
            barra.progress(progreso, f"📄 Procesando página {i+1}/{total_paginas}")
        
        barra.progress(1.0, "✅ Extracción completada")
        doc.close()
        
        # Juntar todo el texto
        texto_completo = "\n\n[=== PAGINA SIGUIENTE ===]\n\n".join(texto_total)
        # Post-procesado: quitar cabeceras/pie de página repetidos, saltar índice y detectar captions
        texto_procesado = post_process_extracted_text(texto_completo)
        return texto_procesado
    except Exception as e:
        st.error(f"Error al abrir o procesar PDF: {e}")
        return ""

def extraer_texto_documento(archivo_subido):
    """Extrae texto de DOCX, TXT o PDF digital."""
    texto_final = ""
    nombre_original = archivo_subido.name
    
    # Intentar importar docx
    try:
        from docx import Document
        docx_available = True
    except ImportError:
        docx_available = False
    
    try:
        if nombre_original.endswith('.docx'):
            if docx_available:
                doc = Document(io.BytesIO(archivo_subido.read()))
                texto_final = "\n".join([para.text for para in doc.paragraphs])
            else:
                raise ImportError("python-docx no está disponible.")
        
        elif nombre_original.endswith('.txt'):
            archivo_subido.seek(0)
            texto_final = archivo_subido.read().decode("utf-8")
        
        elif nombre_original.endswith('.pdf'):
            # Extracción de texto nativo (no OCR)
            archivo_subido.seek(0)
            doc = fitz.open(stream=archivo_subido.read(), filetype="pdf")
            texto_final = ""
            for pagina in doc:
                texto_final += pagina.get_text() + "\n\n"
            doc.close()
        
        return texto_final, nombre_original
        
    except ImportError as e:
        st.error(f"Error: {e}. Por favor, instale la dependencia: pip install python-docx")
        return "", ""
    except Exception as e:
        st.error(f"Error leyendo archivo {nombre_original}: {e}")
        return "", ""


def post_process_extracted_text(texto):
    """Limpieza adicional tras OCR para: 1) eliminar números de página y encabezados repetidos,
    2) saltar el índice si existe, 3) intentar detectar captions de figuras y anteponer una nota.
    Heurísticas simples para mejorar la lectura por TTS.
    """
    if not texto:
        return ""

    # Separador de páginas usado en la extracción
    sep = "\n\n[=== PAGINA SIGUIENTE ===]\n\n"
    pages = [p.strip() for p in texto.split(sep)]
    if not pages:
        return texto

    # 1) Detectar encabezados repetidos (títulos de página que aparecen en muchas páginas)
    first_lines = []
    for p in pages:
        for ln in p.splitlines():
            if ln.strip():
                first_lines.append(ln.strip())
                break
    counts = Counter(first_lines)
    repeated_headers = set([k for k, v in counts.items() if v >= max(2, int(len(pages) * 0.3))])

    cleaned_pages = []
    for p in pages:
        lines = p.splitlines()
        # eliminar encabezado repetido al inicio de página
        if lines and lines[0].strip() in repeated_headers:
            lines = lines[1:]

        # eliminar líneas que parecen números de página o numeración roman
        new_lines = []
        for ln in lines:
            s = ln.strip()
            if re.match(r'^(p(á|a)gina\b|pag\.|page\b)?\s*\d+\s*$', s, re.IGNORECASE):
                continue
            if re.match(r'^[IVXLCM]+\s*$', s):
                continue
            # líneas con muy pocos caracteres y solo números
            if re.match(r'^\d{1,3}$', s):
                continue
            new_lines.append(ln)

        cleaned_pages.append("\n".join(new_lines).strip())

    combined = sep.join(cleaned_pages)

    # 2) Saltar índice/tabla de contenido si existe
    lower = combined.lower()
    index_kw = None
    for kw in ["índice", "indice", "tabla de contenidos", "contenido"]:
        if kw in lower:
            index_kw = kw
            break
    if index_kw:
        # buscar la línea que contiene la palabra clave y cortar desde la siguiente línea
        lines = combined.splitlines()
        start_idx = 0
        for i, ln in enumerate(lines):
            if index_kw in ln.lower():
                start_idx = i + 1
                break
        # avanzar hasta que encontremos una línea vacía seguido de texto (evitar cortar en medio)
        combined = "\n".join(lines[start_idx:]).strip()

    # 3) Detectar captions de figuras en cada página y anteponer una nota breve
    pages2 = [p for p in combined.split(sep)]
    processed_pages = []
    for p in pages2:
        caption = None
        for ln in p.splitlines():
            if re.search(r'\b(figura|fig\.|gráfic|grafico|imagen|fig)\b', ln, re.IGNORECASE):
                caption = ln.strip()
                break
        if caption:
            p = f"Descripción de la figura: {caption}\n\n" + p
        processed_pages.append(p.strip())

    return sep.join(processed_pages).strip()

# ================= VERIFICACIÓN DE LIBRERÍAS =================
def verificar_librerias():
    """Verifica si las librerías opcionales están instaladas."""
    try:
        from docx import Document
        docx_ok = True
    except ImportError:
        docx_ok = False
        
    try:
        from pydub import AudioSegment
        pydub_ok = True
    except ImportError:
        pydub_ok = False
        
    return docx_ok, pydub_ok
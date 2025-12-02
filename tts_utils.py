# tts_utils.py
import asyncio
import edge_tts
import tempfile
import os
import streamlit as st
from ocr_utils import limpiar_texto # Importar la función de limpieza

VOCES = {
    "🇪🇸 Álvaro (España)": "es-ES-AlvaroNeural",
    "🇪🇸 Elvira (España)": "es-ES-ElviraNeural",
    "🇦🇷 Tomás (Argentina)": "es-AR-TomasNeural",
    "🇦🇷 Elena (Argentina)": "es-AR-ElenaNeural",
    "🇲🇽 Dalia (México)": "es-MX-DaliaNeural",
    "🇺🇸 Aria (Inglés USA)": "en-US-AriaNeural",
}

async def generar_audio_async(texto_limpio, voz_codigo, pydub_ok):
    """Función asíncrona para generar el audio usando edge-tts."""
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        ruta_final = tmp.name
    
    # Chunking: Dividir texto para evitar límites de TTS
    MAX_CHARS = 8000
    
    try:
        # Importar pydub de forma perezosa para evitar fallos en import global
        AudioSegment = None
        if pydub_ok:
            try:
                from pydub import AudioSegment as _AudioSegment
                AudioSegment = _AudioSegment
            except Exception as ie:
                # Si falla la importación, desactivar funcionalidades relacionadas
                st.warning(f"Advertencia: falló la importación de pydub ({ie}). Se usará modo sin unión de partes.")
                AudioSegment = None

        if len(texto_limpio) > MAX_CHARS and AudioSegment is not None:
            st.info(f"El texto es largo ({len(texto_limpio):,} caracteres). Dividiendo para unificar el audio...")

            # Dividir por bloques de caracteres, no por oraciones, para Edge TTS
            partes = [texto_limpio[i:i + MAX_CHARS] for i in range(0, len(texto_limpio), MAX_CHARS)]
            audio_completo = AudioSegment.empty()

            # Generar y unir partes
            for i, parte in enumerate(partes):
                st.text(f"Procesando fragmento {i+1}/{len(partes)}...")
                comunicador = edge_tts.Communicate(parte, voz_codigo)
                ruta_parte = f"{ruta_final}_parte{i}.mp3"
                await comunicador.save(ruta_parte) # Bloquea el thread hasta que se guarda

                audio = AudioSegment.from_mp3(ruta_parte)
                audio_completo += audio
                os.remove(ruta_parte)

            audio_completo.export(ruta_final, format="mp3")

        else:
            if len(texto_limpio) > MAX_CHARS and AudioSegment is None:
                st.warning(f"pydub no está disponible. Limitando a los primeros {MAX_CHARS} caracteres.")
                texto_a_tts = texto_limpio[:MAX_CHARS]
            else:
                texto_a_tts = texto_limpio

            comunicador = edge_tts.Communicate(texto_a_tts, voz_codigo)
            await comunicador.save(ruta_final)

        return ruta_final

    except Exception as e:
        st.error(f"Error generando audio: {e}")
        # Limpieza si falla
        if os.path.exists(ruta_final):
            os.remove(ruta_final)
        return None

def generar_audio(texto, voz_codigo, nombre_base, pydub_ok):
    """Llamada principal para generar y descargar el audio."""
    
    texto_limpio = limpiar_texto(texto)
    
    if not texto_limpio or len(texto_limpio.strip()) < 50:
        st.error("Texto insuficiente para generar audio.")
        return
        
    with st.spinner("Generando audio... (Puede tardar si es un texto largo)"):
        # edge-tts es asíncrono, necesitamos ejecutarlo con asyncio.run()
        ruta_audio = asyncio.run(generar_audio_async(texto_limpio, voz_codigo, pydub_ok))
    
    if ruta_audio and os.path.exists(ruta_audio):
        st.success("✅ Audiolibro generado")
        
        # Reproductor
        st.audio(ruta_audio, format="audio/mp3")
        
        # Descarga
        with open(ruta_audio, "rb") as f:
            nombre_descarga = os.path.splitext(nombre_base)[0] + "_audiolibro.mp3"
            st.download_button(
                "⬇️ Descargar MP3",
                f.read(),
                nombre_descarga,
                "audio/mp3",
                use_container_width=True,
                key="dl_audio"
            )
        
        os.remove(ruta_audio)
    else:
        st.error("Error generando audio.")
        
    return texto_limpio # Devolvemos el texto limpio para métricas
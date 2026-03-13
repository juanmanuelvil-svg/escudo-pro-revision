import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import tempfile
import os
import urllib.parse

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Escudo Ciudadano", page_icon="🛡️", layout="centered")

# --- DISEÑO VISUAL ---
st.markdown("<h1 style='text-align: center; color: #198754;'>🛡️ ESCUDO CIUDADANO</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #495057;'>Módulo de Atención Plurilingüe</h4>", unsafe_allow_html=True)
st.divider()

# --- SEGURIDAD: EXTRACCIÓN DE LA LLAVE ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ Falta configurar la Llave API en los Secrets del servidor.")
    st.stop()

# --- 1. DATOS DEL CIUDADANO ---
st.subheader("Paso 1: ¿Quién eres y a quién le escribes?")
col1, col2 = st.columns(2)
with col1:
    nombre = st.text_input("👤 Tu Nombre Completo:", value=st.session_state.get('nombre_val', ""))
with col2:
    contacto = st.text_input("📍 Domicilio, Teléfono o e-mail:", value=st.session_state.get('contacto_val', ""))

dependencia = st.text_input("🏢 ¿A qué oficina del gobierno va dirigido?", value=st.session_state.get('dep_val', ""))
dep_final = dependencia if dependencia else "Autoridad Competente"

# --- 2. TRÁMITE ---
st.subheader("Paso 2: ¿Qué necesitas hacer?")
tipo_tramite = st.selectbox("Selecciona una opción:", [
    "📝 Hacer una Petición (Queja de calle, bache, luz, agua, etc.)",
    "❓ Pedir Información Pública (Transparencia / Presupuestos)",
    "🛡️ Defender mis derechos (Multa injusta, cobro excesivo, despido)",
    "🏥 Solicitar un Servicio (Atención médica, beca, apoyo social)"
])

# --- 3. HISTORIA Y ACCESIBILIDAD PLURILINGÜE ---
st.subheader("Paso 3: Detalles y Evidencia")
st.info("💡 **JUSTICIA INCLUSIVA:** Si hablas Español, Náhuatl, Maya, Tseltal, Tsotsil, Mixteco o Zapoteco, graba tu voz aquí. La IA activará tus derechos lingüísticos y redactará el documento en español formal.")

audio_grabado = st.audio_input("🎤 Toca para grabar tu voz (Español o Lengua Originaria)")
historia_texto = st.text_area("⌨️ O si prefieres, escríbelo aquí manualmente:", height=100, value=st.session_state.get('historia_val', ""))

st.subheader("📸 Evidencia (Opcional)")
archivo_evidencia = st.file_uploader("Sube una foto de tu multa o documento:", type=['png', 'jpg', 'jpeg', 'pdf', 'mp3', 'wav', 'm4a'])

st.divider()

# --- FUNCIÓN PARA GENERAR WORD ---
def crear_word(texto_oficio):
    doc = Document()
    estilo = doc.styles['Normal']
    estilo.font.name = 'Arial'
    estilo.font.size = Pt(12)
    for linea in texto_oficio.split('\n'):
        if linea.strip():
            p = doc.add_paragraph(linea.strip())
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    return archivo_memoria.getvalue()

# --- ZONA DE BOTONES ---
col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 1])

with col_btn1:
    btn_generar = st.button("✨ REDACTAR DEFENSA LEGAL", use_container_width=True, type="primary")

with col_btn2:
    if 'oficio_generado' in st.session_state:
        word_bytes = crear_word(st.session_state['oficio_generado'])
        st.download_button(
            label="💾 DESCARGAR EN WORD",
            data=word_bytes,
            file_name=f"Peticion_{nombre.replace(' ', '_')}.docx" if nombre else "Peticion_Legal.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True
        )
    else:
        st.button("💾 DESCARGAR EN WORD", disabled=True, use_container_width=True)

with col_btn3:
    if st.button("🗑️ LIMPIAR", use_container_width=True):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

# --- LÓGICA DE INTELIGENCIA ARTIFICIAL CON DOBLE REVISIÓN ---
if btn_generar:
    if not nombre:
        st.warning("⚠️ Por favor ingresa tu Nombre para continuar.")
    elif not historia_texto and not audio_grabado:
        st.warning("⚠️ Cuéntanos tu problema por voz o texto.")
    else:
        with st.status("⚙️ Procesando tu caso legal...", expanded=True) as status:
            archivos_temporales = []
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # --- PASO 1: REDACCIÓN DEL BORRADOR ---
                status.update(label="⏳ Paso 1/2: El Abogado Virtual está analizando y redactando el borrador...", state="running")
                contenido_prompt = []

                prompt_borrador = f"""
                ERES UN ABOGADO PRO BONO MEXICANO, EXPERTO EN DERECHO ADMINISTRATIVO Y PUEBLOS INDÍGENAS.
                Tu tarea es usar todo tu conocimiento legal para estructurar y fundamentar este oficio.
                
                REGLA DE ORO ESTRICTA: El documento final DEBE estar redactado SIEMPRE en PRIMERA PERSONA del singular ("yo", "solicito", "comparezco"), como si el propio ciudadano afectado lo estuviera redactando y presentándolo "por su propio derecho". 
                
                SI HAY AUDIO: Escucha si es ESPAÑOL, NÁHUATL, MAYA, TSELTAL, TSOTSIL, MIXTECO o ZAPOTECO.
                Si es lengua indígena, incluye al inicio de los hechos: "Manifiesto ser hablante de la lengua [LENGUA] y solicito asistencia de intérprete conforme al Art. 2º Constitucional."

                DATOS DEL CIUDADANO: 
                Nombre: {nombre}
                Contacto: {contacto}
                AUTORIDAD DESTINATARIA: {dep_final}
                TIPO DE TRÁMITE: {tipo_tramite}
                HISTORIA/HECHOS: {historia_texto if historia_texto else 'Revisar audio.'}
                
                FORMATO: Texto plano puro (SIN asteriscos ni Markdown). 
                Estructura: Lugar y Fecha (deja espacio), Destinatario, PRESENTE., Asunto, Proemio (compareciendo por mi propio derecho), Hechos, Peticiones enumeradas, Protesto lo necesario, Firma directa del ciudadano ({nombre}).
                """
                
                if audio_grabado:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as t:
                        t.write(audio_grabado.getvalue())
                        archivos_temporales.append(t.name)
                        audio_ia = genai.upload_file(t.name)
                        contenido_prompt.append(audio_ia)

                if archivo_evidencia:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{archivo_evidencia.name.split('.')[-1]}") as t:
                        t.write(archivo_evidencia.getvalue())
                        archivos_temporales.append(t.name)
                        evid_ia = genai.upload_file(t.name)
                        contenido_prompt.append(evid_ia)

                contenido_prompt.append(prompt_borrador)
                respuesta_borrador = model.generate_content(contenido_prompt)
                texto_borrador = respuesta_borrador.text
                
                # --- PASO 2: FILTRO ANTI-ALUCINACIONES ---
                status.update(label="🔍 Paso 2/2: El Juez Revisor está verificando que las leyes y artículos sean reales...", state="running")
                
                prompt_revision = f"""
                ERES UN REVISOR LEGAL MEXICANO ESTRICTO (Socio de Despacho).
                Tu única tarea es leer el siguiente borrador de un oficio y ELIMINAR CUALQUIER ALUCINACIÓN DE IA.
                
                REGLAS ESTRICTAS:
                1. Si el borrador cita un Artículo, Ley o Reglamento del que NO estás 100% seguro de que existe y es vigente en México (especialmente reglamentos municipales específicos), BÓRRALO y adapta la redacción.
                2. Es preferible fundamentar con el "Artículo 8 Constitucional (Derecho de Petición)" y principios generales de derecho, a que inventes una ley.
                3. Mantén intacta la redacción en PRIMERA PERSONA ("yo, comparezco").
                4. Devuelve ÚNICAMENTE el texto final corregido y limpio (sin asteriscos, sin negritas, sin formato markdown).
                
                BORRADOR A REVISAR Y CORREGIR:
                {texto_borrador}
                """
                
                respuesta_final = model.generate_content(prompt_revision)
                texto_limpio = respuesta_final.text.replace("**", "").replace("*", "").replace("#", "")
                
                st.session_state['oficio_generado'] = texto_limpio
                status.update(label="✅ ¡Documento verificado y fundamentado con éxito!", state="complete", expanded=False)
                st.rerun()

            except Exception as e:
                status.update(label="❌ Error durante el proceso.", state="error")
                st.error(f"Detalle del error: {e}")
            finally:
                for ruta in archivos_temporales:
                    if os.path.exists(ruta): os.remove(ruta)

# --- MOSTRAR RESULTADO ---
if 'oficio_generado' in st.session_state:
    st.success("✅ ¡Documento generado con éxito!")
    st.text_area("Vista Previa del Documento:", value=st.session_state['oficio_generado'], height=350)
    
    # --- NUEVO: BOTÓN DE WHATSAPP ---
    st.write("¿Deseas enviar este borrador por WhatsApp para impresión rápida?")
    mensaje_amigable = f"Hola, necesito ayuda para imprimir este documento oficial:\n\n{st.session_state['oficio_generado']}"
    mensaje_codificado = urllib.parse.quote(mensaje_amigable)
    link_whatsapp = f"https://api.whatsapp.com/send?text={mensaje_codificado}"
    st.link_button("📲 ENVIAR POR WHATSAPP", url=link_whatsapp)

# --- 7. AVISOS LEGALES Y DE PRIVACIDAD ---
st.write("---")
st.markdown("<h5 style='text-align: center; color: #6c757d;'>Información Legal y Transparencia</h5>", unsafe_allow_html=True)

with st.expander("⚖️ AVISO LEGAL Y LÍMITES DE RESPONSABILIDAD (LEER ANTES DE USAR)"):
    st.markdown("""
    **1. No es Asesoría Legal Humana:** "Escudo Ciudadano" es una herramienta tecnológica experimental impulsada por Inteligencia Artificial (IA). No sustituye el consejo, la representación, ni la revisión de un abogado titulado con Cédula Profesional.
    
    **2. Limitaciones de la Tecnología:** La Inteligencia Artificial puede cometer errores, citar artículos derogados, o interpretar incorrectamente el contexto o la traducción de lenguas originarias (alucinaciones de IA).
    
    **3. Responsabilidad del Usuario:** El documento generado es un "borrador" o "formato sugerido". Es responsabilidad absoluta y exclusiva del usuario leer, verificar, corregir y validar el contenido, los fundamentos legales y sus datos personales antes de firmarlo o presentarlo ante cualquier autoridad.
    
    **4. Deslinde de Responsabilidad:** El creador de este software y la plataforma de alojamiento no asumen ninguna responsabilidad legal, civil, penal o administrativa por el resultado de los trámites, rechazos de autoridades, daños, o perjuicios derivados del uso de los textos generados por este sistema.
    """)

with st.expander("🔒 AVISO DE PRIVACIDAD SIMPLIFICADO"):
    st.markdown("""
    De conformidad con la Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP), se informa lo siguiente:
    
    **1. Identidad del Responsable:** El proyecto independiente "Escudo Ciudadano" (desarrollado por Juan Manuel Villegas) es el responsable del tratamiento temporal de los datos recabados en este sitio.
    
    **2. Datos Recabados y Finalidad:** Los datos personales proporcionados (nombre, contacto, descripción de hechos, audios y fotografías de evidencia) se utilizarán **exclusivamente** para redactar y estructurar el documento legal solicitado en tiempo real.
    
    **3. Almacenamiento y Borrado:** Esta plataforma NO almacena sus datos en bases de datos permanentes. La información existe únicamente durante su sesión activa (memoria caché) y se elimina irreversiblemente al presionar el botón "Limpiar" o al cerrar el navegador.
    
    **4. Transferencia de Datos:** Para poder funcionar, los textos, audios e imágenes se procesan de manera cifrada a través de las interfaces de programación (APIs) de Google y Streamlit. Al usar esta plataforma, usted consiente este procesamiento automatizado de terceros para la generación de su documento.
    """)

st.caption("© 2026 Escudo Ciudadano v1.0 | Desarrollado para el Acceso a la Justicia Social en México.")

import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import speech_to_text
from streamlit_TTS import text_to_speech

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="إرشاد Mornigag", layout="wide")

# --- 2. الإعدادات العامة ---
PRODUCT_NAME = "Mornigag"
GEMINI_API_KEY = "AIzaSyDpjmc3mMO4q4KP1MvHMXOsOL_k5M6-umA"

# تهيئة المكتبة المستقرة
genai.configure(api_key=GEMINI_API_KEY)

def format_bidi_text(text, lang):
    if lang == 'Arabic':
        return f'<div style="direction: rtl; text-align: right;">{text}</div>'
    return text

# --- 3. النصوص المطلوبة ---
def get_texts(lang):
    instr_ar = "للبدء، انقر على أيقونة **انقر للتحدث** ثم تحدث، وبعد الانتهاء انقر عليها مرة أخرى."
    instr_en = "To start, click on the **Click to Speak** icon, then talk, and click it again when finished."
    
    if lang == 'English':
        return {
            'title': f"**{PRODUCT_NAME}** Counselling",
            'instructions': instr_en,
            'input_hint': "Type here...",
            'stt_lang': 'en', 'tts_lang': 'en'
        }
    else:
        return {
            'title': f"إرشاد دواء **{PRODUCT_NAME}**",
            'instructions': instr_ar,
            'input_hint': "اكتب رسالتك هنا...",
            'stt_lang': 'ar', 'tts_lang': 'ar'
        }

# --- 4. الواجهة ---
selected_lang = st.sidebar.selectbox("Language / اللغة", ["Arabic", "English"])
texts = get_texts(selected_lang)

st.markdown(f"## {texts['title']}")
with st.expander("Instructions / تعليمات", expanded=True):
    st.markdown(texts['instructions'])

# --- 5. إدارة الجلسة ---
if "messages" not in st.session_state:
    st.session_state.messages = []

@st.cache_resource
def get_model():
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_model()

# --- 6. الإدخال ---
c1, c2 = st.columns([1, 4])
with c1:
    spoken = speech_to_text(language=texts['stt_lang'], start_prompt="🎙️", stop_prompt="⏹️", just_once=True, key=f"mic_{selected_lang}")
with c2:
    written = st.text_input("in", key=f"txt_{selected_lang}", label_visibility="collapsed", placeholder=texts['input_hint'])

user_input = spoken if spoken else written

# --- 7. العرض والمعالجة ---
container = st.container()
for m in st.session_state.messages:
    with container:
        st.chat_message(m["role"]).markdown(format_bidi_text(m["content"], selected_lang), unsafe_allow_html=True)

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with container:
        st.chat_message("user").markdown(format_bidi_text(user_input, selected_lang), unsafe_allow_html=True)
    
    with st.spinner("..."):
        try:
            prompt = f"System: You are a Patient Educator for {PRODUCT_NAME}. Speak in {selected_lang} only.\n\n"
            for m in st.session_state.messages[-5:]:
                prompt += f"{m['role']}: {m['content']}\n"
            
            response = model.generate_content(prompt)
            ai_text = response.text
            
            st.session_state.messages.append({"role": "assistant", "content": ai_text})
            with container:
                st.chat_message("assistant", avatar="👩‍⚕️").markdown(format_bidi_text(ai_text, selected_lang), unsafe_allow_html=True)
            
            text_to_speech(text=ai_text, language=texts['tts_lang'], key=f"v_{hash(ai_text)}")
            st.rerun()
        except Exception as e:
            st.error("خطأ في الاتصال. يرجى التأكد من تحديث ملف requirements.txt")

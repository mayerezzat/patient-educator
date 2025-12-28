import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import speech_to_text
from streamlit_TTS import text_to_speech

# --- إعدادات الصفحة ---
st.set_page_config(page_title="إرشاد Mornigag", layout="wide")

# --- الإعدادات العامة ---
PRODUCT_NAME = "Mornigag"
GEMINI_API_KEY = "AIzaSyDpjmc3mMO4q4KP1MvHMXOsOL_k5M6-umA"

# تهيئة Gemini (الحل الجذري لخطأ 404)
try:
    genai.configure(api_key=GEMINI_API_KEY)
    # نستخدم الموديل بدون كلمة models/ في البداية لتجنب تعارض الإصدارات
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("خطأ في تهيئة المفتاح")

def format_bidi_text(text, lang):
    if lang == 'Arabic':
        return f'<div style="direction: rtl; text-align: right;">{text}</div>'
    return text

# --- النصوص المطلوبة ---
def get_texts(lang):
    # النص الذي طلبته بالضبط
    instr_ar = "للبدء، انقر على أيقونة **انقر للتحدث** ثم تحدث، وبعد الانتهاء انقر عليها مرة أخرى."
    instr_en = "To start, click on the **Click to Speak** icon, then talk, and click it again when finished."
    
    if lang == 'English':
        return {
            'title': f"**{PRODUCT_NAME}** Counselling",
            'instructions': instr_en,
            'hint': "Type here...",
            'stt_lang': 'en', 'tts_lang': 'en'
        }
    else:
        return {
            'title': f"إرشاد دواء **{PRODUCT_NAME}**",
            'instructions': instr_ar,
            'hint': "اكتب هنا...",
            'stt_lang': 'ar', 'tts_lang': 'ar'
        }

# --- الواجهة ---
selected_lang = st.sidebar.selectbox("Language / اللغة", ["Arabic", "English"])
texts = get_texts(selected_lang)

st.markdown(f"## {texts['title']}")
with st.expander("Instructions / تعليمات", expanded=True):
    st.markdown(texts['instructions'])

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- الإدخال ---
c1, c2 = st.columns([1, 4])
with c1:
    spoken = speech_to_text(language=texts['stt_lang'], start_prompt="🎙️", stop_prompt="⏹️", just_once=True, key=f"mic_{selected_lang}")
with c2:
    written = st.text_input("in", key=f"txt_{selected_lang}", label_visibility="collapsed", placeholder=texts['hint'])

user_input = spoken if spoken else written

# --- المعالجة ---
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
            # صياغة الطلب بطريقة بسيطة ومستقرة
            prompt_context = f"You are a professional Patient Educator for {PRODUCT_NAME}. Respondent is Sarah. Respond in {selected_lang} only. Question: {user_input}"
            response = model.generate_content(prompt_context)
            ai_text = response.text
            
            st.session_state.messages.append({"role": "assistant", "content": ai_text})
            with container:
                st.chat_message("assistant", avatar="👩‍⚕️").markdown(format_bidi_text(ai_text, selected_lang), unsafe_allow_html=True)
            
            text_to_speech(text=ai_text, language=texts['tts_lang'], key=f"v_{hash(ai_text)}")
            st.rerun()
        except Exception as e:
            st.error(f"حدث خطأ: {str(e)}")

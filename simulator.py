import streamlit as st
import google.generativeai as genai # المكتبة المستقرة
from streamlit_mic_recorder import speech_to_text
from streamlit_TTS import text_to_speech

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="إرشاد Mornigag", 
    layout="wide"
)

# --- 2. الإعدادات العامة ---
PRODUCT_NAME = "Mornigag"
GEMINI_API_KEY = "AIzaSyDpjmc3mMO4q4KP1MvHMXOsOL_k5M6-umA"

# تهيئة الـ API بالطريقة المستقرة
genai.configure(api_key=GEMINI_API_KEY)

def format_bidi_text(text, lang):
    if lang == 'Arabic':
        return f'<div style="direction: rtl; text-align: right;">{text}</div>'
    return text

# --- 3. النصوص المطلوبة ---
def get_texts(lang):
    # النص الذي طلبته بالضبط
    instr_ar = "للبدء، انقر على أيقونة **انقر للتحدث** ثم تحدث، وبعد الانتهاء انقر عليها مرة أخرى."
    instr_en = "To start, click on the **Click to Speak** icon, then talk, and click it again when finished."

    if lang == 'English':
        return {
            'title': f"**{PRODUCT_NAME}** Counselling", 
            'instructions': instr_en,
            'sidebar_title': "🎙️ Settings",
            'lang_label': "Language",
            'speak_prompt': "Click to Speak (🎙️)",
            'stop_prompt': "Stop Recording (⏹️)",
            'input_placeholder': "Type here...",
            'thinking': "AI is thinking...",
            'stt_lang': 'en',
            'tts_lang': 'en'
        }
    else:
        return {
            'title': f"إرشاد دواء **{PRODUCT_NAME}**", 
            'instructions': instr_ar,
            'sidebar_title': "🎙️ الإعدادات",
            'lang_label': "اللغة",
            'speak_prompt': "انقر للتحدث (🎙️)",
            'stop_prompt': "إيقاف التسجيل (⏹️)",
            'input_placeholder': "اكتب هنا...",
            'thinking': "جاري المعالجة...",
            'stt_lang': 'ar',
            'tts_lang': 'ar'
        }

# --- 4. واجهة المستخدم ---
selected_lang = st.sidebar.selectbox("Language", ["Arabic", "English"], index=0)
texts = get_texts(selected_lang)

st.markdown(f"## {texts['title']}")
with st.expander("Instructions", expanded=True):
    st.markdown(texts['instructions'])

# --- 5. إدارة الجلسة (الحل الجذري لـ 404) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# استخدام GenerativeModel المباشر لتجنب مشاكل الـ Chat Session
@st.cache_resource
def load_model():
    return genai.GenerativeModel('gemini-1.5-flash')

model = load_model()

# --- 6. الإدخال ---
col1, col2 = st.columns([1, 4])
with col1:
    spoken = speech_to_text(language=texts['stt_lang'], start_prompt=texts['speak_prompt'], stop_prompt=texts['stop_prompt'], just_once=True, key=f"mic_{selected_lang}")
with col2:
    written = st.text_input("Input", key=f"in_{selected_lang}", label_visibility="collapsed", placeholder=texts['input_placeholder'])

user_input = spoken if spoken else written

# --- 7. المعالجة والعرض ---
chat_container = st.container()

# عرض التاريخ
for m in st.session_state.messages:
    with chat_container:
        st.chat_message(m["role"]).markdown(format_bidi_text(m["content"], selected_lang), unsafe_allow_html=True)

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with chat_container:
        st.chat_message("user").markdown(format_bidi_text(user_input, selected_lang), unsafe_allow_html=True)
    
    with st.spinner(texts['thinking']):
        try:
            # استخدام generate_content بدلاً من send_message لحل مشكلة الـ 404 نهائياً
            sys_msg = f"Role: Patient Educator for {PRODUCT_NAME}. Patient: Sarah. Language: {selected_lang}. Respond briefly."
            full_prompt = f"{sys_msg}\n\nHistory: {st.session_state.messages}\n\nUser: {user_input}"
            
            response = model.generate_content(full_prompt)
            ai_text = response.text
            
            st.session_state.messages.append({"role": "assistant", "content": ai_text})
            with chat_display := st.container():
                st.chat_message("assistant", avatar="👩‍⚕️").markdown(format_bidi_text(ai_text, selected_lang), unsafe_allow_html=True)
                text_to_speech(text=ai_text, language=texts['tts_lang'], key=f"v_{hash(ai_text)}")
            st.rerun()
        except Exception as e:
            st.error("Connection Error. Please check your API key or Refresh.")

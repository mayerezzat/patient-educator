import streamlit as st
from google import genai
from google.genai import types
from streamlit_mic_recorder import speech_to_text
from streamlit_TTS import text_to_speech
import os

# --- إعدادات الصفحة ---
st.set_page_config(page_title="Patient Simulator", layout="wide")

# --- جلب المفتاح من Secrets ---
if "GEMINI_API_KEY" in st.secrets:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("⚠️ يرجى إضافة GEMINI_API_KEY في إعدادات Secrets")
    st.stop()

@st.cache_resource
def get_gemini_client():
    try:
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        st.stop()

client = get_gemini_client()

# --- وظائف التنسيق ---
def format_bidi_text(text, lang):
    if lang == 'Arabic':
        return f'<div style="direction: rtl; text-align: right;">{text}</div>'
    return text

# --- واجهة المستخدم ---
selected_language = st.sidebar.selectbox("اللغة / Language", ["Arabic", "English"])

if selected_language == "Arabic":
    texts = {
        "title": "محاكي إرشاد المريض",
        "welcome": "أهلاً بك، أنا مثقف المريض. كيف يمكنني مساعدتك اليوم؟",
        "input_label": "تحدث أو اكتب سؤالك هنا:",
        "spinner": "جاري التفكير..."
    }
else:
    texts = {
        "title": "Patient Simulator",
        "welcome": "Hello, I am your Patient Educator. How can I help you?",
        "input_label": "Speak or type your question:",
        "spinner": "Thinking..."
    }

st.title(texts["title"])

# --- إدارة المحادثة ---
if "chat_session" not in st.session_state:
    config = types.GenerateContentConfig(system_instruction=f"You are a Patient Educator. {texts['welcome']}")
    st.session_state.chat_session = client.chats.create(model="gemini-2.0-flash", config=config)

chat_session = st.session_state.chat_session

# --- منطقة الإدخال ---
col1, col2 = st.columns([1, 4])
with col1:
    spoken_text = speech_to_text(language='ar' if selected_language=='Arabic' else 'en', start_prompt="🎙️", stop_prompt="⏹️", key='mic')
with col2:
    written_text = st.text_input(texts["input_label"], key='text_input')

user_input = spoken_text if spoken_text else written_text

if user_input:
    with st.spinner(texts["spinner"]):
        response = chat_session.send_message(user_input)
        ai_response = response.text
        text_to_speech(text=ai_response, language='ar' if selected_language=='Arabic' else 'en', key=f"tts_{len(chat_session.get_history())}")

# عرض الرسائل
for msg in chat_session.get_history():
    if msg.role != "system":
        role = "user" if msg.role == "user" else "assistant"
        st.chat_message(role).markdown(format_bidi_text(msg.parts[0].text, selected_language), unsafe_allow_html=True)

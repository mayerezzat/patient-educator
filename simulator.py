import streamlit as st
from google import genai
from google.genai import types
from streamlit_mic_recorder import speech_to_text
from streamlit_TTS import text_to_speech
import os
import datetime 

# --- إعدادات الواجهة والصفحة ---
st.set_page_config(
    page_title="Patient Counselling Simulator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- إعدادات المنتج وجلب المفتاح من Secrets ---
PRODUCT_NAME = "Mornigag"

# جلب المفتاح بأمان من إعدادات Streamlit Cloud
if "GEMINI_API_KEY" in st.secrets:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("⚠️ لم يتم العثور على المفتاح! يرجى إضافته في إعدادات Secrets باسم GEMINI_API_KEY")
    st.stop()

@st.cache_resource
def get_gemini_client():
    """تهيئة عميل Gemini - تم تصحيح api_key هنا"""
    try:
        # التصحيح: api_key هو الاسم الصحيح للبارامتر
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        st.error(f"خطأ في تهيئة عميل Gemini: {e}")
        st.stop() 

client = get_gemini_client()

# --- وظائف التنسيق والنصوص ---
def format_bidi_text(text, lang):
    if lang == 'Arabic':
        return f'<div style="direction: rtl; unicode-bidi: embed; text-align: right;">{text}</div>'
    return text

def get_texts(lang):
    if lang == 'English':
        return {
            'title': f"Patient Counselling: **{PRODUCT_NAME}**",
            'instructions': "Your role is the **Patient**. The AI is the **Educator**.",
            'speak_prompt': "Click to Speak (🎙️)",
            'stop_prompt': "Stop (⏹️)",
            'thinking_spinner': "AI is thinking...",
            'gemini_model': "gemini-2.0-flash",
            'tts_lang_code': 'en',
            'welcome_msg': f"Hello, I am your Patient Educator. We are discussing {PRODUCT_NAME}. Can you please tell me your name?"
        }
    else:
        return {
            'title': f"إرشاد المريض: **{PRODUCT_NAME}**",
            'instructions': "دورك هو **المريض**. الذكاء الاصطناعي هو **المثقف**.",
            'speak_prompt': "انقر للتحدث (🎙️)",
            'stop_prompt': "إيقاف (⏹️)",
            'thinking_spinner': "الذكاء الاصطناعي يفكر...",
            'gemini_model': "gemini-2.0-flash",
            'tts_lang_code': 'ar',
            'welcome_msg': f"أهلاً بكِ. أنا مثقف المريض الخاص بكِ. نتحدث اليوم عن {PRODUCT_NAME}. هل يمكنكِ إخباري باسمكِ؟"
        }

# --- واجهة المستخدم ---
selected_language = st.sidebar.selectbox("Language / اللغة", ["Arabic", "English"])
texts = get_texts(selected_language)
st.title(texts['title'])
st.info(texts['instructions'])

# --- إدارة الجلسة ---
if "chat_session" not in st.session_state:
    config = types.GenerateContentConfig(
        system_instruction=f"You are a Patient Educator. Be helpful and clear. {texts['welcome_msg']}"
    )
    st.session_state.chat_session = client.chats.create(model=texts['gemini_model'], config=config)

chat_session = st.session_state.chat_session

# --- منطقة المحادثة ---
chat_container = st.container()

col1, col2 = st.columns([1, 4])
with col1:
    spoken_text = speech_to_text(language=texts['tts_lang_code'], start_prompt=texts['speak_prompt'], stop_prompt=texts['stop_prompt'], key='mic_input')
with col2:
    written_text = st.text_input("اكتب رسالتك هنا...", key='text_input')

user_input = spoken_text if spoken_text else written_text

if user_input:
    with st.spinner(texts['thinking_spinner']):
        try:
            response = chat_session.send_message(user_input)
            ai_response = response.text
            text_to_speech(text=ai_response, language=texts['tts_lang_code'], key=f"tts_{len(chat_session.get_history())}")
        except Exception as e:
            st.error(f"حدث خطأ أثناء الاتصال: {e}")

# عرض الرسائل من التاريخ
for msg in chat_session.get_history():
    if msg.role != "system":
        with chat_container:
            role = "user" if msg.role == "user" else "assistant"
            st.chat_message(role).markdown(format_bidi_text(msg.parts[0].text, selected_language), unsafe_allow_html=True)

import streamlit as st
from google import genai
from google.genai import types
from streamlit_mic_recorder import speech_to_text
from streamlit_TTS import text_to_speech
import os

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="إرشاد Mornigag", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. الإعدادات العامة ---
PRODUCT_NAME = "Mornigag"
GEMINI_API_KEY = "AIzaSyDpjmc3mMO4q4KP1MvHMXOsOL_k5M6-umA"

@st.cache_resource
def get_gemini_client():
    try:
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        st.stop()

client = get_gemini_client()

def format_bidi_text(text, lang):
    if lang == 'Arabic':
        return f'<div style="direction: rtl; unicode-bidi: embed; text-align: right;">{text}</div>'
    return text

# --- 3. النصوص (تم حذف الجملة المطلوبة وتعديل التعليمات) ---
def get_texts(lang):
    instruction_ar = "للبدء، انقر على أيقونة **انقر للتحدث** ثم تحدث، وبعد الانتهاء انقر عليها مرة أخرى."
    instruction_en = "To start, click on the **Click to Speak** icon, then talk, and click it again when finished."

    if lang == 'English':
        return {
            'title': f"**{PRODUCT_NAME}** Counselling", 
            'subheader': "Simulated Session",
            'instructions': instruction_en,
            'sidebar_title': "🎙️ Settings",
            'lang_select': "Language",
            'speed_slider': "Speech Speed",
            'accent_select': "Tone",
            'your_response': "🎤 **Your Message**",
            'speak_prompt': "Click to Speak (🎙️)",
            'stop_prompt': "Stop Recording (⏹️)",
            'chat_input_prompt': "Type here...",
            'thinking_spinner': "AI is processing...",
            'model_name': "gemini-2.0-flash-exp", # تم التغيير لتجنب خطأ 404
            'tts_lang': 'en',
            'stt_lang': 'en'
        }
    else:
        return {
            'title': f"إرشاد دواء **{PRODUCT_NAME}**", 
            'subheader': "وضع المحاكاة",
            'instructions': instruction_ar,
            'sidebar_title': "🎙️ الإعدادات",
            'lang_select': "اللغة",
            'speed_slider': "سرعة الكلام",
            'accent_select': "نمط المعلم",
            'your_response': "🎤 **رسالتك**",
            'speak_prompt': "انقر للتحدث (🎙️)",
            'stop_prompt': "إيقاف التسجيل (⏹️)",
            'chat_input_prompt': "اكتب هنا...",
            'thinking_spinner': "جاري المعالجة...",
            'model_name': "gemini-2.0-flash-exp",
            'tts_lang': 'ar',
            'stt_lang': 'ar'
        }

# --- 4. شريط الإعدادات ---
selected_lang = st.sidebar.selectbox("Language", ["Arabic", "English"], index=0)
texts = get_texts(selected_lang)
tts_speed = st.sidebar.slider(texts['speed_slider'], 0.5, 2.0, 1.2)
selected_accent = st.sidebar.selectbox(texts['accent_select'], ["متعاطف", "رسمي", "مباشر"])

# --- 5. الواجهة الرئيسية ---
st.markdown(f"## {texts['title']}")
with st.expander("Instructions", expanded=True):
    st.markdown(texts['instructions'])

# --- 6. إدارة الجلسة ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# حل مشكلة الـ 404 باستخدام الموديل الجديد وفصل الجلسات
session_key = f"chat_session_{selected_lang}"
if session_key not in st.session_state:
    sys_prompt = f"You are a Patient Educator for {PRODUCT_NAME}. Respond in {selected_lang} only."
    st.session_state[session_key] = client.chats.create(
        model=texts['model_name'],
        config=types.GenerateContentConfig(system_instruction=sys_prompt)
    )

# --- 7. الإدخال والمعالجة ---
input_col1, input_col2 = st.columns([1, 4])
with input_col1:
    spoken = speech_to_text(language=texts['stt_lang'], start_prompt=texts['speak_prompt'], stop_prompt=texts['stop_prompt'], just_once=True, key=f"stt_{selected_lang}")
with input_col2:
    written = st.text_input(texts['chat_input_prompt'], key=f"txt_{selected_lang}", label_visibility="collapsed")

user_input = spoken if spoken else written

chat_display = st.container()

# عرض التاريخ
for msg in st.session_state.messages:
    with chat_display:
        st.chat_message(msg["role"], avatar=msg.get("avatar")).markdown(format_bidi_text(msg["content"], selected_lang), unsafe_allow_html=True)

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input, "avatar": None})
    with chat_display:
        st.chat_message("user").markdown(format_bidi_text(user_input, selected_lang), unsafe_allow_html=True)
    
    with st.spinner(texts['thinking_spinner']):
        try:
            response = st.session_state[session_key].send_message(user_input)
            ai_text = response.text
            st.session_state.messages.append({"role": "assistant", "content": ai_text, "avatar": "👩‍⚕️"})
            with chat_display:
                st.chat_message("assistant", avatar="👩‍⚕️").markdown(format_bidi_text(ai_text, selected_lang), unsafe_allow_html=True)
            text_to_speech(text=ai_text, language=texts['tts_lang'], key=f"tts_{hash(ai_text)}")
            st.rerun()
        except Exception as e:
            st.error(f"خطأ في توليد الرد: {e}")

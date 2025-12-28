import streamlit as st
from google import genai
from google.genai import types
from streamlit_mic_recorder import speech_to_text
from streamlit_TTS import text_to_speech
import os
import datetime 

# --- 1. إعدادات الواجهة والصفحة ---
st.set_page_config(
    page_title="Patient Counselling Simulator", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. إعدادات API والمنتج ---
PRODUCT_NAME = "Mornigag"
GEMINI_API_KEY = "AIzaSyDpjmc3mMO4q4KP1MvHMXOsOL_k5M6-umA"

@st.cache_resource
def get_gemini_client():
    try:
        # استخدام الإصدار الأحدث من مكتبة google-genai
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        st.error(f"خطأ في تهيئة عميل Gemini: {e}")
        st.stop() 

client = get_gemini_client()

# وظيفة تنسيق النصوص للعربية
def format_bidi_text(text, lang):
    if lang == 'Arabic':
        return f'<div style="direction: rtl; unicode-bidi: embed; text-align: right;">{text}</div>'
    return text

# --- 3. تعريف النصوص (مع التعديل المطلوب) ---
def get_texts(lang):
    # الجملة التي طلبتها بالضبط
    instruction_msg_ar = "للبدء، انقر على أيقونة **انقر للتحدث** ثم تحدث، وبعد الانتهاء انقر عليها مرة أخرى."
    instruction_msg_en = "To start, click on the **Click to Speak** icon, then talk, and click it again when finished."

    if lang == 'English':
        return {
            'title': f"Patient Counselling: **AI Educator** for **{PRODUCT_NAME}**",
            'subheader': "Simulation Mode",
            'instructions': instruction_msg_en,
            'sidebar_title': "🎙️ Settings",
            'lang_select': "Select Language",
            'speed_slider': "Speech Speed",
            'accent_select': "Educator Style",
            'your_response': "🎤 **Your Message**",
            'speak_prompt': "Click to Speak (🎙️)",
            'stop_prompt': "Stop Recording (⏹️)",
            'chat_input_prompt': "Type here...",
            'thinking_spinner': "AI is thinking...",
            'accent_options': ["Empathetic", "Formal", "Direct"],
            'gemini_model': "gemini-1.5-flash", # موديل ثابت
            'tts_lang_code': 'en',
            'stt_lang_code': 'en',
            'welcome_msg': f"Hello, I am your Patient Educator. I understand you've been prescribed **{PRODUCT_NAME}**. Before we start, what is your name?"
        }
    else: # Arabic
        return {
            'title': f"محاكاة إرشاد المريض: **الذكاء الاصطناعي كمعلم** لدواء **{PRODUCT_NAME}**",
            'subheader': "وضع المحاكاة",
            'instructions': instruction_msg_ar,
            'sidebar_title': "🎙️ الإعدادات",
            'lang_select': "اختيار اللغة",
            'speed_slider': "سرعة الكلام",
            'accent_select': "نمط المعلم",
            'your_response': "🎤 **رسالتك**",
            'speak_prompt': "انقر للتحدث (🎙️)",
            'stop_prompt': "إيقاف التسجيل (⏹️)",
            'chat_input_prompt': "اكتب هنا...",
            'thinking_spinner': "الذكاء الاصطناعي يفكر...",
            'accent_options': ["متعاطف", "رسمي", "مباشر"],
            'gemini_model': "gemini-1.5-flash",
            'tts_lang_code': 'ar',
            'stt_lang_code': 'ar',
            'welcome_msg': f"أهلاً بكِ، أنا مثقف المريض الخاص بكِ. أفهم أنه وُصِفَ لكِ دواء **{PRODUCT_NAME}**. قبل أن نبدأ، هل يمكنكِ إخباري باسمكِ؟"
        }

# --- 4. واجهة المستخدم ---
selected_language = st.sidebar.selectbox("Language", options=["Arabic", "English"], index=0)
texts = get_texts(selected_language)
tts_speed = st.sidebar.slider(texts['speed_slider'], 0.5, 2.0, 1.2)
selected_accent = st.sidebar.selectbox(texts['accent_select'], texts['accent_options'])

st.markdown(f"## {texts['title']}")
with st.expander("Instructions", expanded=True):
    st.markdown(texts['instructions'])

# --- 5. منطق الـ Chat Session ---
def get_system_prompt(lang, accent, welcome):
    if lang == 'Arabic':
        return f"أنت خبير تثقيف مرضى. أسلوبك {accent}. المريضة سارة. ابدأ دائماً بـ: {welcome}"
    return f"You are a Patient Educator. Style: {accent}. Patient is Sarah. Start with: {welcome}"

current_prompt = get_system_prompt(selected_language, selected_accent, texts['welcome_msg'])

if "chat_session" not in st.session_state or st.session_state.get('lang') != selected_language:
    st.session_state.lang = selected_language
    config = types.GenerateContentConfig(system_instruction=current_prompt)
    st.session_state.chat_session = client.chats.create(model="gemini-1.5-flash", config=config)

# --- 6. الإدخال والمعالجة ---
input_col1, input_col2 = st.columns([1, 4])
with input_col1:
    spoken_text = speech_to_text(language=texts['stt_lang_code'], start_prompt=texts['speak_prompt'], stop_prompt=texts['stop_prompt'], just_once=True, key='stt')
with input_col2:
    written_text = st.text_input(texts['chat_input_prompt'], key='txt_input', label_visibility="collapsed")

user_msg = spoken_text if spoken_text else written_text

chat_container = st.container()

if user_msg:
    with chat_container:
        st.chat_message("user").markdown(format_bidi_text(user_msg, selected_language), unsafe_allow_html=True)
        with st.spinner(texts['thinking_spinner']):
            try:
                response = st.session_state.chat_session.send_message(user_msg)
                answer = response.text
                st.chat_message("assistant", avatar="👩‍⚕️").markdown(format_bidi_text(answer, selected_language), unsafe_allow_html=True)
                text_to_speech(text=answer, language=texts['tts_lang_code'], key=f"tts_{hash(answer)}")
            except Exception as e:
                st.error(f"Error: {e}")

# عرض التاريخ لضمان بقاء المحادثة أمام المستخدم
for msg in st.session_state.chat_session.get_history():
    if msg.role != "system":
        role = "user" if msg.role == "user" else "assistant"
        with chat_container:
            st.chat_message(role, avatar="👩‍⚕️" if role == "assistant" else None).markdown(format_bidi_text(msg.parts[0].text, selected_language), unsafe_allow_html=True)

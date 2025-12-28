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

# --- إعدادات المنتج والعميل ---
PRODUCT_NAME = "Mornigag"
GEMINI_API_KEY = "AIzaSyDpjmc3mMO4q4KP1MvHMXOsOL_k5M6-umA"

@st.cache_resource
def get_gemini_client():
    try:
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        st.error(f"خطأ في تهيئة عميل Gemini: {e}")
        st.stop() 

client = get_gemini_client()

def format_bidi_text(text, lang):
    if lang == 'Arabic':
        return f'<div style="direction: rtl; unicode-bidi: embed; text-align: right;">{text}</div>'
    return text

# --- التعديل الجذري في النصوص هنا ---
def get_texts(lang):
    speak_instruction_arabic = "للبدء، انقر على أيقونة **انقر للتحدث** ثم تحدث، وبعد الانتهاء انقر عليها مرة أخرى."
    speak_instruction_english = "To start, click on the **Click to Speak** icon, then talk, and click it again when finished."

    if lang == 'English':
        return {
            'title': f"Patient Counselling Simulation: **AI as Educator** for **{PRODUCT_NAME}**",
            'subheader': "Simulated Patient Educator Role-Play",
            'instructions': f"{speak_instruction_english}", # تم حذف "Your role is..."
            'sidebar_title': "🎙️ Simulation Settings",
            'lang_select': "1. Select Language",
            'speed_slider': "2. Speech Speed (1.0 = Normal)",
            'accent_select': "3. Patient Educator Tone/Style",
            'your_response': "🎤 **Your Patient Question/Concern**",
            'speak_prompt': "Click to Speak (🎙️)",
            'stop_prompt': "Stop Recording (⏹️)",
            'chat_input_prompt': "Type your question here...",
            'thinking_spinner': "AI Educator is counselling...",
            'transcribed_text': "Transcribed Text:",
            'error': "An API error occurred:",
            'accent_options': ["Empathetic & Clear", "Formal & Technical", "Quick & Direct"],
            'gemini_model': "gemini-1.5-flash",
            'tts_lang_code': 'en',
            'stt_lang_code': 'en',
            'feedback_button': "Generate AI Educator Self-Assessment Report 📄",
            'feedback_spinner': "AI is generating report...",
            'feedback_title': f"AI Educator Self-Assessment Report: {PRODUCT_NAME}",
            'welcome_msg': f"Hello, welcome. I am your Patient Educator. I understand you've been prescribed **{PRODUCT_NAME}** for NVP. Before we start, can you please tell me your name?"
        }
    else: # Arabic
        return {
            'title': f"محاكاة إرشاد المريض: **الذكاء الاصطناعي كمعلم** لدواء **{PRODUCT_NAME}**",
            'subheader': "لعب دور المريض لتقييم أداء المعلم",
            'instructions': f"{speak_instruction_arabic}", # تم حذف "دورك هو المريض..."
            'sidebar_title': "🎙️ إعدادات المحاكاة",
            'lang_select': "1. اختيار اللغة",
            'speed_slider': "2. سرعة الكلام (1.0 = عادي)",
            'accent_select': "3. نمط/نبرة مثقف المريض",
            'your_response': "🎤 **سؤال/قلقك كمريض**",
            'speak_prompt': "انقر للتحدث (🎙️)",
            'stop_prompt': "إيقاف التسجيل (⏹️)",
            'chat_input_prompt': "اكتب سؤالك أو قلقك كمريض هنا...",
            'thinking_spinner': "مثقف المريض (AI) يقدم الإرشاد...",
            'transcribed_text': "النص المنسوخ:",
            'error': "حدث خطأ أثناء استدعاء API:",
            'accent_options': ["متعاطف وواضح", "رسمي وتقني", "سريع ومباشر"],
            'gemini_model': "gemini-1.5-flash",
            'tts_lang_code': 'ar',
            'stt_lang_code': 'ar',
            'feedback_button': "إنشاء تقرير تقييم ذاتي لمثقف المريض (AI) 📄",
            'feedback_spinner': "الذكاء الاصطناعي يحلل أداءه ويولد التقرير...",
            'feedback_title': f"تقرير التقييم الذاتي لمثقف المريض (AI): {PRODUCT_NAME}",
            'welcome_msg': f"أهلاً، مرحباً بكِ. أنا مثقف المريض الخاص بكِ. أفهم أنه وُصِفَ لكِ دواء **{PRODUCT_NAME}** لغثيان وقيء الحمل (NVP). قبل أن نبدأ، هل يمكنكِ إخباري باسمكِ؟"
        }

# --- بقية الكود الأساسي ---
selected_language = st.sidebar.selectbox("1. اختيار اللغة", options=["Arabic", "English"], index=0)
texts = get_texts(selected_language)

st.sidebar.title(texts['sidebar_title'])
tts_speed = st.sidebar.slider(texts['speed_slider'], min_value=0.5, max_value=2.0, value=1.2, step=0.1)
selected_accent = st.sidebar.selectbox(texts['accent_select'], options=texts['accent_options'], index=0)

main_container = st.container()
with main_container:
    st.markdown(f"## {texts['title']}")
    st.subheader(texts['subheader'])
    with st.expander("Session Instructions", expanded=True):
        st.markdown(texts['instructions'])

def get_system_instruction(lang, accent, welcome_msg):
    if lang == 'English':
        educator_persona = f"You are a highly skilled, knowledgeable, and **{accent}** Patient Educator. The user is Sarah. Respond ONLY in English."
    else:
        educator_persona = f"أنت مثقف مريض ذو مهارات عالية ونبرتك **{accent}**. المستخدم مريضة حامل اسمها سارة. الرد فقط باللغة العربية."
        
    return f"""
    You are the Patient Educator. The user is the Patient (Sarah).
    Product: {PRODUCT_NAME} (Doxylamine/Pyridoxine) for NVP.
    {educator_persona}
    1. Start exactly with: "{welcome_msg}"
    2. Wait for name, then explain dosage and safety.
    """

current_system_instruction = get_system_instruction(selected_language, selected_accent, texts['welcome_msg'])
current_state_key = f"{selected_language}_{selected_accent}_{PRODUCT_NAME}_final"

if "chat_session" not in st.session_state or st.session_state.get('current_state_key') != current_state_key:
    st.session_state.current_state_key = current_state_key
    st.session_state.user_name = None
    config = types.GenerateContentConfig(system_instruction=current_system_instruction)
    st.session_state.chat_session = client.chats.create(model=texts['gemini_model'], config=config)

chat_session = st.session_state.chat_session

input_container = st.container()
with input_container:
    st.markdown("---")
    st.markdown(texts['your_response'])
    col1, col2 = st.columns([1, 4]) 
    with col1:
        spoken_text = speech_to_text(language=texts['stt_lang_code'], start_prompt=texts['speak_prompt'], stop_prompt=texts['stop_prompt'], just_once=True, key='stt_btn')
    with col2:
        written_text = st.text_input(texts['chat_input_prompt'], label_visibility="collapsed", key='chat_input')
    user_input = spoken_text if spoken_text else written_text

chat_history_container = st.container()
if user_input:
    with chat_history_container:
        st.chat_message("user").markdown(format_bidi_text(user_input, selected_language), unsafe_allow_html=True)
        with st.spinner(texts['thinking_spinner']):
            response = chat_session.send_message(user_input)
            st.chat_message("assistant", avatar="👩‍⚕️").markdown(format_bidi_text(response.text, selected_language), unsafe_allow_html=True)
            text_to_speech(text=response.text, language=texts['tts_lang_code'], key=f"tts_{hash(response.text)}")

# عرض الرسائل القديمة
for message in chat_session.get_history():
    if message.role != "system":
        role = "user" if message.role == "user" else "assistant"
        avatar = "👩‍⚕️" if role == "assistant" else None
        with chat_history_container:
            st.chat_message(role, avatar=avatar).markdown(format_bidi_text(message.parts[0].text, selected_language), unsafe_allow_html=True)

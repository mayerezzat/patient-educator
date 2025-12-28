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

# --- إعدادات المنتج وجلب المفتاح بأمان ---
PRODUCT_NAME = "Mornigag"

# جلب المفتاح من Secrets (يجب إضافته في إعدادات Streamlit Cloud)
if "GEMINI_API_KEY" in st.secrets:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("⚠️ لم يتم العثور على مفتاح GEMINI_API_KEY في إعدادات Secrets.")
    st.stop()

@st.cache_resource
def get_gemini_client():
    """تجهيز عميل Gemini باستخدام المفتاح الصحيح"""
    try:
        # التصحيح: api_key هو البارامتر الصحيح
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        st.error(f"خطأ في تهيئة عميل Gemini: {e}")
        st.stop() 

client = get_gemini_client()

# --- وظيفة لتنسيق النص ودعم اتجاهات الكتابة (RTL) ---
def format_bidi_text(text, lang):
    if lang == 'Arabic':
        return f'<div style="direction: rtl; unicode-bidi: embed; text-align: right;">{text}</div>'
    return text

# --- تعريف النصوص الديناميكية للواجهة ---
def get_texts(lang):
    speak_instruction_arabic = "للبدء، انقر على أيقونة **انقر للتحدث** ثم تحدث، وبعد الانتهاء انقر عليها مرة أخرى."
    speak_instruction_english = "To start, click on the **Click to Speak** icon, then talk, and click it again when finished."

    if lang == 'English':
        return {
            'title': f"Patient Counselling Simulation: **AI as Educator** for **{PRODUCT_NAME}**",
            'subheader': "Simulated Patient Educator Role-Play",
            'instructions': f"Your role is the **Patient** (Mrs. Sarah). The AI is the **Patient Educator**. Ask questions about safety, dosage, and side effects. **{speak_instruction_english}**",
            'sidebar_title': "🎙️ Simulation Settings",
            'lang_select': "1. Select Language",
            'speed_slider': "2. Speech Speed",
            'accent_select': "3. Patient Educator Tone",
            'your_response': "🎤 **Your Patient Question/Concern**",
            'speak_prompt': "Click to Speak (🎙️)",
            'stop_prompt': "Stop Recording (⏹️)",
            'chat_input_prompt': "Type your question here...",
            'thinking_spinner': "AI Educator is counselling...",
            'transcribed_text': "Transcribed Text:",
            'error': "An API error occurred:",
            'accent_options': ["Empathetic & Clear", "Formal & Technical", "Quick & Direct"],
            'gemini_model': "gemini-2.0-flash", # إصدار مستقر
            'tts_lang_code': 'en',
            'stt_lang_code': 'en',
            'feedback_button': "Generate AI Educator Report 📄",
            'feedback_spinner': "Generating report...",
            'feedback_title': f"AI Educator Self-Assessment: {PRODUCT_NAME}",
            'welcome_msg': f"Hello, I am your Patient Educator. I understand you've been prescribed **{PRODUCT_NAME}**. Before we start, can you please tell me your name?"
        }
    else:
        return {
            'title': f"محاكاة إرشاد المريض: **الذكاء الاصطناعي كمعلم** لدواء **{PRODUCT_NAME}**",
            'subheader': "لعب دور المريض لتقييم أداء المعلم",
            'instructions': f"دورك هو **المريض** (السيدة سارة). الذكاء الاصطناعي هو **مثقف المريض**. **{speak_instruction_arabic}**",
            'sidebar_title': "🎙️ إعدادات المحاكاة",
            'lang_select': "1. اختيار اللغة",
            'speed_slider': "2. سرعة الكلام",
            'accent_select': "3. نمط مثقف المريض",
            'your_response': "🎤 **سؤالك كمريض**",
            'speak_prompt': "انقر للتحدث (🎙️)",
            'stop_prompt': "إيقاف التسجيل (⏹️)",
            'chat_input_prompt': "اكتب سؤالك هنا...",
            'thinking_spinner': "المثقف (AI) يرد الآن...",
            'transcribed_text': "النص المنسوخ:",
            'error': "حدث خطأ:",
            'accent_options': ["متعاطف وواضح", "رسمي وتقني", "سريع ومباشر"],
            'gemini_model': "gemini-2.0-flash",
            'tts_lang_code': 'ar',
            'stt_lang_code': 'ar',
            'feedback_button': "إنشاء تقرير تقييم ذاتي 📄",
            'feedback_spinner': "يتم تحليل المحادثة...",
            'feedback_title': f"تقرير التقييم الذاتي: {PRODUCT_NAME}",
            'welcome_msg': f"أهلاً بكِ. أنا مثقف المريض الخاص بكِ. أفهم أنه وُصِفَ لكِ دواء **{PRODUCT_NAME}**. قبل أن نبدأ، هل يمكنكِ إخباري باسمكِ؟"
        }

# --- الشريط الجانبي ---
selected_language = st.sidebar.selectbox("1. اختيار اللغة", options=["Arabic", "English"], index=0)
texts = get_texts(selected_language)
st.sidebar.title(texts['sidebar_title'])
tts_speed = st.sidebar.slider(texts['speed_slider'], 0.5, 2.0, 1.2)
selected_accent = st.sidebar.selectbox(texts['accent_select'], options=texts['accent_options'])

# --- نظام المحادثة ---
def get_system_instruction(lang, accent, welcome_msg):
    if lang == 'English':
        persona = f"You are a {accent} Patient Educator. The user is a pregnant patient (Sarah) prescribed {PRODUCT_NAME}. Respond ONLY in English."
    else:
        persona = f"أنت مثقف مريض بأسلوب {accent}. المستخدم مريضة حامل (سارة) وُصف لها {PRODUCT_NAME}. رد فقط باللغة العربية."
    
    return f"{persona} Start with: {welcome_msg}. Focus on dosage, safety, and side effects."

current_state_key = f"{selected_language}_{selected_accent}_{PRODUCT_NAME}"

if "chat_session" not in st.session_state or st.session_state.get('current_state_key') != current_state_key:
    st.session_state.current_state_key = current_state_key
    st.session_state.user_name = None
    config = types.GenerateContentConfig(system_instruction=get_system_instruction(selected_language, selected_accent, texts['welcome_msg']))
    st.session_state.chat_session = client.chats.create(model=texts['gemini_model'], config=config)

chat_session = st.session_state.chat_session

# --- واجهة المستخدم ---
st.markdown(f"## {texts['title']}")
with st.expander("تعليمات الجلسة"):
    st.markdown(texts['instructions'])

chat_history_container = st.container()

# إدخال المستخدم
col1, col2 = st.columns([1, 4])
with col1:
    spoken_text = speech_to_text(language=texts['stt_lang_code'], start_prompt=texts['speak_prompt'], stop_prompt=texts['stop_prompt'], key='speech')
with col2:
    written_text = st.text_input(texts['chat_input_prompt'], key='text_input')

user_input = spoken_text if spoken_text else written_text

if user_input:
    with chat_history_container:
        st.chat_message("user").markdown(format_bidi_text(user_input, selected_language), unsafe_allow_html=True)
    
    with st.spinner(texts['thinking_spinner']):
        response = chat_session.send_message(user_input)
        ai_response = response.text
        with chat_history_container:
            st.chat_message("assistant", avatar="👩‍⚕️").markdown(format_bidi_text(ai_response, selected_language), unsafe_allow_html=True)
        text_to_speech(text=ai_response, language=texts['tts_lang_code'], key=f"tts_{len(chat_session.get_history())}")

# عرض التاريخ
for msg in chat_session.get_history():
    if msg.role != "system":
        with chat_history_container:
            st.chat_message("user" if msg.role == "user" else "assistant").markdown(format_bidi_text(msg.parts[0].text, selected_language), unsafe_allow_html=True)

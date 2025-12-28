import streamlit as st
from google import genai
from google.genai import types
from streamlit_mic_recorder import speech_to_text
from streamlit_TTS import text_to_speech
import os
import datetime 

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Patient Counselling Simulator", 
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
        st.error(f"Error initializing Gemini: {e}")
        st.stop()

client = get_gemini_client()

def format_bidi_text(text, lang):
    if lang == 'Arabic':
        return f'<div style="direction: rtl; unicode-bidi: embed; text-align: right;">{text}</div>'
    return text

# --- 3. النصوص (الجملة المطلوبة تم تعديلها هنا) ---
def get_texts(lang):
    instruction_ar = "للبدء، انقر على أيقونة **انقر للتحدث** ثم تحدث، وبعد الانتهاء انقر عليها مرة أخرى."
    instruction_en = "To start, click on the **Click to Speak** icon, then talk, and click it again when finished."

    if lang == 'English':
        return {
            'title': f"Patient Counselling: **AI Educator** for **{PRODUCT_NAME}**",
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
            'thinking_spinner': "AI is thinking...",
            'accent_options': ["Empathetic", "Formal", "Direct"],
            'tts_lang': 'en',
            'stt_lang': 'en',
            'welcome': f"Hello, I am your educator. We are talking about **{PRODUCT_NAME}**. What is your name?"
        }
    else:
        return {
            'title': f"محاكاة إرشاد المريض: **الذكاء الاصطناعي كمعلم** لدواء **{PRODUCT_NAME}**",
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
            'accent_options': ["متعاطف", "رسمي", "مباشر"],
            'tts_lang': 'ar',
            'stt_lang': 'ar',
            'welcome': f"أهلاً بكِ، أنا مثقف المريض الخاص بكِ. أفهم أنه وُصِفَ لكِ دواء **{PRODUCT_NAME}**. قبل أن نبدأ، هل يمكنكِ إخباري باسمكِ؟"
        }

# --- 4. شريط الإعدادات ---
selected_lang = st.sidebar.selectbox("Language", ["Arabic", "English"], index=0)
texts = get_texts(selected_lang)
tts_speed = st.sidebar.slider(texts['speed_slider'], 0.5, 2.0, 1.2)
selected_accent = st.sidebar.selectbox(texts['accent_select'], texts['accent_options'])

st.markdown(f"## {texts['title']}")
with st.expander("Instructions", expanded=True):
    st.markdown(texts['instructions'])

# --- 5. إدارة الجلسة (حل مشكلة ClientError) ---
if "chat_session" not in st.session_state or st.session_state.get('last_lang') != selected_lang:
    st.session_state.last_lang = selected_lang
    sys_prompt = f"You are a Patient Educator. Style: {selected_accent}. Patient: Sarah. Product: {PRODUCT_NAME}. Respond in {selected_lang} only."
    
    st.session_state.chat_session = client.chats.create(
        model="gemini-1.5-flash",
        config=types.GenerateContentConfig(system_instruction=sys_prompt)
    )
    # تصفير المحادثة عند تغيير اللغة
    st.session_state.messages = []

# --- 6. واجهة الإدخال ---
input_col1, input_col2 = st.columns([1, 4])
with input_col1:
    spoken = speech_to_text(language=texts['stt_lang'], start_prompt=texts['speak_prompt'], stop_prompt=texts['stop_prompt'], just_once=True, key='stt_v3')
with input_col2:
    written = st.text_input(texts['chat_input_prompt'], key='txt_v3', label_visibility="collapsed")

user_input = spoken if spoken else written

# --- 7. معالجة الرسائل والعرض ---
chat_display = st.container()

# عرض التاريخ من session_state بدلاً من الموديل مباشرة لتجنب أخطاء المزامنة
for msg in st.session_state.messages:
    with chat_display:
        st.chat_message(msg["role"], avatar=msg.get("avatar")).markdown(format_bidi_text(msg["content"], selected_lang), unsafe_allow_html=True)

if user_input:
    # 1. إضافة رسالة المستخدم للواجهة
    st.session_state.messages.append({"role": "user", "content": user_input, "avatar": None})
    with chat_display:
        st.chat_message("user").markdown(format_bidi_text(user_input, selected_lang), unsafe_allow_html=True)
    
    # 2. طلب الرد من الذكاء الاصطناعي
    with st.spinner(texts['thinking_spinner']):
        try:
            response = st.session_state.chat_session.send_message(user_input)
            ai_text = response.text
            
            # 3. إضافة رد المعلم للواجهة
            st.session_state.messages.append({"role": "assistant", "content": ai_text, "avatar": "👩‍⚕️"})
            with chat_display:
                st.chat_message("assistant", avatar="👩‍⚕️").markdown(format_bidi_text(ai_text, selected_lang), unsafe_allow_html=True)
            
            # 4. تحويل النص لصوت
            text_to_speech(text=ai_text, language=texts['tts_lang'], key=f"tts_{hash(ai_text)}")
            st.rerun() # تحديث الصفحة لضمان ترتيب الرسائل
        except Exception as e:
            st.error(f"Connection Error: {e}")

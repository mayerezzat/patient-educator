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
        # تهيئة العميل مع تحديد مفتاح الـ API
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        st.error(f"خطأ في الاتصال بـ Gemini: {e}")
        st.stop()

client = get_gemini_client()

def format_bidi_text(text, lang):
    if lang == 'Arabic':
        return f'<div style="direction: rtl; unicode-bidi: embed; text-align: right;">{text}</div>'
    return text

# --- 3. النصوص (تم تعديل التعليمات بناءً على طلبك) ---
def get_texts(lang):
    # الجملة التي طلبتها بالضبط
    instruction_ar = "للبدء، انقر على أيقونة **انقر للتحدث** ثم تحدث، وبعد الانتهاء انقر عليها مرة أخرى."
    instruction_en = "To start, click on the **Click to Speak** icon, then talk, and click it again when finished."

    if lang == 'English':
        return {
            'title': f"Patient Counselling: **AI Educator** for **{PRODUCT_NAME}**",
            'subheader': "Simulation Mode",
            'instructions': instruction_en,
            'sidebar_title': "🎙️ Settings",
            'lang_select': "Language",
            'speed_slider': "Speech Speed",
            'accent_select': "Educator Tone",
            'your_response': "🎤 **Your Message**",
            'speak_prompt': "Click to Speak (🎙️)",
            'stop_prompt': "Stop Recording (⏹️)",
            'chat_input_prompt': "Type here...",
            'thinking_spinner': "AI is processing...",
            'accent_options': ["Empathetic", "Formal", "Direct"],
            'model_name': "gemini-2.0-flash-exp", # الموديل الأحدث والأكثر توافقاً
            'tts_lang': 'en',
            'stt_lang': 'en'
        }
    else:
        return {
            'title': f"محاكاة إرشاد المريض: **الذكاء الاصطناعي كمعلم** لدواء **{PRODUCT_NAME}**",
            'subheader': "وضع المحاكاة",
            'instructions': instruction_ar,
            'sidebar_title': "🎙️ الإعدادات",
            'lang_select': "اختيار اللغة",
            'speed_slider': "سرعة الكلام",
            'accent_select': "نمط المعلم",
            'your_response': "🎤 **رسالتك**",
            'speak_prompt': "انقر للتحدث (🎙️)",
            'stop_prompt': "إيقاف التسجيل (⏹️)",
            'chat_input_prompt': "اكتب هنا...",
            'thinking_spinner': "جاري المعالجة...",
            'accent_options': ["متعاطف", "رسمي", "مباشر"],
            'model_name': "gemini-2.0-flash-exp",
            'tts_lang': 'ar',
            'stt_lang': 'ar'
        }

# --- 4. شريط الإعدادات ---
selected_lang = st.sidebar.selectbox("Language", ["Arabic", "English"], index=0)
texts = get_texts(selected_lang)
tts_speed = st.sidebar.slider(texts['speed_slider'], 0.5, 2.0, 1.2)
selected_accent = st.sidebar.selectbox(texts['accent_select'], texts['accent_options'])

st.markdown(f"## {texts['title']}")
with st.expander("Instructions", expanded=True):
    st.markdown(texts['instructions'])

# --- 5. إدارة الجلسة (حل مشكلة 404) ---
# نستخدم KEY فريد لكل لغة لضمان عدم تداخل التاريخ
session_key = f"chat_{selected_lang}"

if session_key not in st.session_state:
    sys_prompt = f"You are a Patient Educator for {PRODUCT_NAME}. Style: {selected_accent}. Patient: Sarah. Respond in {selected_lang} only."
    
    # محاولة إنشاء الجلسة بموديل 2.0 فلاش
    try:
        st.session_state[session_key] = client.chats.create(
            model=texts['model_name'],
            config=types.GenerateContentConfig(system_instruction=sys_prompt)
        )
        st.session_state[f"history_{selected_lang}"] = []
    except Exception:
        # إذا فشل 2.0، نستخدم 1.5-flash كخطة احتياطية
        st.session_state[session_key] = client.chats.create(
            model="gemini-1.5-flash",
            config=types.GenerateContentConfig(system_instruction=sys_prompt)
        )
        st.session_state[f"history_{selected_lang}"] = []

# --- 6. واجهة الإدخال ---
input_col1, input_col2 = st.columns([1, 4])
with input_col1:
    spoken = speech_to_text(language=texts['stt_lang'], start_prompt=texts['speak_prompt'], stop_prompt=texts['stop_prompt'], just_once=True, key=f"stt_{selected_lang}")
with input_col2:
    written = st.text_input(texts['chat_input_prompt'], key=f"txt_{selected_lang}", label_visibility="collapsed")

user_input = spoken if spoken else written

# --- 7. معالجة الرسائل والعرض ---
chat_display = st.container()

# عرض التاريخ المخزن
for msg in st.session_state[f"history_{selected_lang}"]:
    with chat_display:
        st.chat_message(msg["role"], avatar=msg.get("avatar")).markdown(format_bidi_text(msg["content"], selected_lang), unsafe_allow_html=True)

if user_input:
    # إضافة رسالة المستخدم للتاريخ
    st.session_state[f"history_{selected_lang}"].append({"role": "user", "content": user_input, "avatar": None})
    with chat_display:
        st.chat_message("user").markdown(format_bidi_text(user_input, selected_lang), unsafe_allow_html=True)
    
    with st.spinner(texts['thinking_spinner']):
        try:
            # إرسال الرسالة
            response = st.session_state[session_key].send_message(user_input)
            ai_text = response.text
            
            # إضافة رد المعلم للتاريخ
            st.session_state[f"history_{selected_lang}"].append({"role": "assistant", "content": ai_text, "avatar": "👩‍⚕️"})
            with chat_display:
                st.chat_message("assistant", avatar="👩‍⚕️").markdown(format_bidi_text(ai_text, selected_lang), unsafe_allow_html=True)
            
            # تشغيل الصوت
            text_to_speech(text=ai_text, language=texts['tts_lang'], key=f"tts_{hash(ai_text)}")
            st.rerun()
        except Exception as e:
            st.error(f"خطأ في توليد الرد: {e}")

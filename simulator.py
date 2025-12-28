import streamlit as st
import google.generativeai as genai # المكتبة المستقرة والأساسية
from streamlit_mic_recorder import speech_to_text
from streamlit_TTS import text_to_speech
import os

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="إرشاد Mornigag", 
    layout="wide"
)

# --- 2. الإعدادات العامة ---
PRODUCT_NAME = "Mornigag"
GEMINI_API_KEY = "AIzaSyDpjmc3mMO4q4KP1MvHMXOsOL_k5M6-umA"

# تهيئة الـ API بالمكتبة المستقرة
genai.configure(api_key=GEMINI_API_KEY)

def format_bidi_text(text, lang):
    if lang == 'Arabic':
        return f'<div style="direction: rtl; unicode-bidi: embed; text-align: right;">{text}</div>'
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
            'speak_prompt': "انقر للتحدث (🎙️)",
            'stop_prompt': "إيقاف التسجيل (⏹️)",
            'input_placeholder': "اكتب سؤالك هنا كمريض...",
            'thinking': "جاري المعالجة...",
            'stt_lang': 'ar',
            'tts_lang': 'ar'
        }

# --- 4. واجهة المستخدم ---
selected_lang = st.sidebar.selectbox("Language / اللغة", ["Arabic", "English"], index=0)
texts = get_texts(selected_lang)

st.markdown(f"## {texts['title']}")
with st.expander("Instructions / تعليمات", expanded=True):
    st.markdown(texts['instructions'])

# --- 5. إدارة الجلسة (الحل النهائي لخطأ 404) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# تعريف الموديل وبدء المحادثة
if "chat_session" not in st.session_state or st.session_state.get('last_lang') != selected_lang:
    st.session_state.last_lang = selected_lang
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=f"You are a helpful Patient Educator for {PRODUCT_NAME}. Respondent is Sarah. Respond in {selected_lang} only."
    )
    st.session_state.chat_session = model.start_chat(history=[])

# --- 6. الإدخال (صوت + كتابة) ---
col1, col2 = st.columns([1, 4])
with col1:
    spoken = speech_to_text(language=texts['stt_lang'], start_prompt=texts['speak_prompt'], stop_prompt=texts['stop_prompt'], just_once=True, key=f"mic_{selected_lang}")
with col2:
    written = st.text_input("Input", key=f"txt_{selected_lang}", label_visibility="collapsed", placeholder=texts['input_placeholder'])

user_input = spoken if spoken else written

# --- 7. العرض والمعالجة ---
chat_container = st.container()

# عرض المحادثة السابقة
for m in st.session_state.messages:
    with chat_container:
        st.chat_message(m["role"]).markdown(format_bidi_text(m["content"], selected_lang), unsafe_allow_html=True)

if user_input:
    # حفظ رسالة المستخدم
    st.session_state.messages.append({"role": "user", "content": user_input})
    with chat_container:
        st.chat_message("user").markdown(format_bidi_text(user_input, selected_lang), unsafe_allow_html=True)
    
    with st.spinner(texts['thinking']):
        try:
            # إرسال الرسالة عبر المكتبة المستقرة
            response = st.session_state.chat_session.send_message(user_input)
            ai_text = response.text
            
            # حفظ رد المعلم
            st.session_state.messages.append({"role": "assistant", "content": ai_text})
            with chat_container:
                st.chat_message("assistant", avatar="👩‍⚕️").markdown(format_bidi_text(ai_text, selected_lang), unsafe_allow_html=True)
            
            # تشغيل الصوت تلقائياً
            text_to_speech(text=ai_text, language=texts['tts_lang'], key=f"aud_{hash(ai_text)}")
            st.rerun()
        except Exception as e:
            st.error("Connection Error: Please refresh the page.")

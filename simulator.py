import streamlit as st
import google.generativeai as genai  # استخدام المكتبة المستقرة
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

# تهيئة Gemini بالمكتبة المستقرة
genai.configure(api_key=GEMINI_API_KEY)

def format_bidi_text(text, lang):
    if lang == 'Arabic':
        return f'<div style="direction: rtl; unicode-bidi: embed; text-align: right;">{text}</div>'
    return text

# --- 3. النصوص (تم حذف الجملة وتعديل التعليمات بناءً على طلبك) ---
def get_texts(lang):
    # النص الذي طلبته بالضبط
    instruction_ar = "للبدء، انقر على أيقونة **انقر للتحدث** ثم تحدث، وبعد الانتهاء انقر عليها مرة أخرى."
    instruction_en = "To start, click on the **Click to Speak** icon, then talk, and click it again when finished."

    if lang == 'English':
        return {
            'title': f"**{PRODUCT_NAME}** Counselling", 
            'instructions': instruction_en,
            'sidebar_title': "🎙️ Settings",
            'lang_select': "Language",
            'speed_slider': "Speech Speed",
            'your_response': "🎤 **Your Message**",
            'speak_prompt': "Click to Speak (🎙️)",
            'stop_prompt': "Stop Recording (⏹️)",
            'chat_input_prompt': "Type here...",
            'thinking_spinner': "AI is processing...",
            'tts_lang': 'en',
            'stt_lang': 'en'
        }
    else:
        return {
            'title': f"إرشاد دواء **{PRODUCT_NAME}**", 
            'instructions': instruction_ar,
            'sidebar_title': "🎙️ الإعدادات",
            'lang_select': "اللغة",
            'speed_slider': "سرعة الكلام",
            'your_response': "🎤 **رسالتك**",
            'speak_prompt': "انقر للتحدث (🎙️)",
            'stop_prompt': "إيقاف التسجيل (⏹️)",
            'chat_input_prompt': "اكتب هنا...",
            'thinking_spinner': "جاري المعالجة...",
            'tts_lang': 'ar',
            'stt_lang': 'ar'
        }

# --- 4. شريط الإعدادات ---
selected_lang = st.sidebar.selectbox("Language", ["Arabic", "English"], index=0)
texts = get_texts(selected_lang)
tts_speed = st.sidebar.slider(texts['speed_slider'], 0.5, 2.0, 1.2)

# --- 5. الواجهة الرئيسية ---
st.markdown(f"## {texts['title']}")
with st.expander("Instructions", expanded=True):
    st.markdown(texts['instructions'])

# --- 6. إدارة الجلسة (الحل النهائي لخطأ 404) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# إعادة ضبط الجلسة عند تغيير اللغة
if "chat_session" not in st.session_state or st.session_state.get('last_lang') != selected_lang:
    st.session_state.last_lang = selected_lang
    # إنشاء الموديل باستخدام المكتبة المستقرة
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=f"You are a helpful Patient Educator for {PRODUCT_NAME}. Patient is Sarah. Respond in {selected_lang} only."
    )
    st.session_state.chat_session = model.start_chat(history=[])

# --- 7. الإدخال (صوت وكتابة) ---
input_col1, input_col2 = st.columns([1, 4])
with input_col1:
    spoken = speech_to_text(language=texts['stt_lang'], start_prompt=texts['speak_prompt'], stop_prompt=texts['stop_prompt'], just_once=True, key=f"mic_{selected_lang}")
with input_col2:
    written = st.text_input(texts['chat_input_prompt'], key=f"input_{selected_lang}", label_visibility="collapsed")

user_input = spoken if spoken else written

# --- 8. معالجة وعرض المحادثة ---
chat_display = st.container()

# عرض التاريخ المخزن في الجلسة
for m in st.session_state.messages:
    with chat_display:
        st.chat_message(m["role"], avatar=m.get("avatar")).markdown(format_bidi_text(m["content"], selected_lang), unsafe_allow_html=True)

if user_input:
    # حفظ رسالة المستخدم وعرضها
    st.session_state.messages.append({"role": "user", "content": user_input, "avatar": None})
    with chat_display:
        st.chat_message("user").markdown(format_bidi_text(user_input, selected_lang), unsafe_allow_html=True)
    
    with st.spinner(texts['thinking_spinner']):
        try:
            # إرسال الرسالة عبر المكتبة المستقرة
            response = st.session_state.chat_session.send_message(user_input)
            ai_text = response.text
            
            # حفظ رد المعلم وعرضه
            st.session_state.messages.append({"role": "assistant", "content": ai_text, "avatar": "👩‍⚕️"})
            with chat_display:
                st.chat_message("assistant", avatar="👩‍⚕️").markdown(format_bidi_text(ai_text, selected_lang), unsafe_allow_html=True)
            
            # تشغيل الصوت تلقائياً
            text_to_speech(text=ai_text, language=texts['tts_lang'], key=f"audio_{hash(ai_text)}")
            st.rerun()
        except Exception as e:
            st.error("خطأ في الاتصال. يرجى التأكد من أن مكتبة google-generativeai مضافة في requirements.txt")

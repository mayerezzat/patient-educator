import streamlit as st
from google import genai
from google.genai import types
from streamlit_mic_recorder import speech_to_text
from streamlit_TTS import text_to_speech
import os
import datetime 

# --- إعدادات الواجهة ---
st.set_page_config(page_title="Patient Counselling Simulator", layout="wide")

# --- جلب المفتاح من Secrets بأمان ---
# تأكد من إضافة GEMINI_API_KEY في إعدادات Streamlit Cloud Secrets
try:
    GEMINI_API_KEY = st.secrets["AIzaSyDpjmc3mMO4q4KP1MvHMXOsOL_k5M6-umA"]
except:
    st.error("لم يتم العثور على المفتاح! يرجى إضافته في إعدادات Secrets.")
    st.stop()

@st.cache_resource
def get_gemini_client():
    try:
        return genai.Client(api_api_key=AIzaSyDpjmc3mMO4q4KP1MvHMXOsOL_k5M6-umA)
    except Exception as e:
        st.error(f"خطأ في تهيئة Gemini: {e}")
        st.stop()

client = get_gemini_client()

# بقية الكود الخاص بك كما هو...
# (للاختصار، أكمل بقية وظائف الـ Bidi و الـ Chat Session هنا)



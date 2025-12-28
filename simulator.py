import streamlit as st
from google import genai
from google.genai import types
from streamlit_mic_recorder import speech_to_text
from streamlit_TTS import text_to_speech
import os
import datetime 

# --- إعدادات الواجهة والصفحة ---
st.set_page_config(
    page_title="Patient Counselling Simulator", # Updated title
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- إعدادات المنتج والعميل ---
# يمكنك تغيير هذه القيم لتغيير المنتج المستهدف واللغة
PRODUCT_NAME = "Mornigag"
COMPETITOR_NAME = "Dostinex" 
# الصق مفتاح Gemini API الفعلي الخاص بك هنا:
GEMINI_API_KEY = "AIzaSyDpjmc3mMO4q4KP1MvHMXOsOL_k5M6-umA"

@st.cache_resource
def get_gemini_client():
    """Initializes and caches the Gemini client."""
    try:
        # Check if the API key is not the placeholder before trying to initialize
        if not GEMINI_API_KEY or GEMINI_API_KEY == "AIzaSyDeVsRlh8fDA7g-E7cNRKHM2E_LAiAxTAI":
             # In a real app, this would be retrieved securely. For this demo, we proceed.
             pass 
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        st.error(f"خطأ في تهيئة عميل Gemini: {e}. يرجى التحقق من تنسيق مفتاح API.")
        st.stop() 

client = get_gemini_client()

# --- وظيفة لتنسيق النص ودعم اتجاهات الكتابة المختلفة (Bidi Support) ---
def format_bidi_text(text, lang):
    """
    Wraps text content in HTML with direction and unicode-bidi styles 
    to correctly handle mixed RTL (Arabic) and LTR (English) content.
    """
    if lang == 'Arabic':
        # استخدام اتجاه اليمين لليسار (rtl) مع تضمين العناصر ذات الاتجاه الآخر
        return f'<div style="direction: rtl; unicode-bidi: embed; text-align: right;">{text}</div>'
    return text

# --- 2. تعريف النصوص الديناميكية للواجهة ---
def get_texts(lang):
    """Returns all UI texts based on the selected language."""
    # التعليمات الإضافية لزر التحدث
    speak_instruction_arabic = "للبدء، انقر على أيقونة **انقر للتحدث** ثم تحدث، وبعد الانتهاء انقر عليها مرة أخرى."
    speak_instruction_english = "To start, click on the **Click to Speak** icon, then talk, and click it again when finished."

    if lang == 'English':
        return {
            'title': f"Patient Counselling Simulation: **AI as Educator** for **{PRODUCT_NAME}**", # Updated
            'subheader': "Simulated Patient Educator Role-Play", # Updated
            'instructions': f"Your role is the **Patient** (Mrs. Sarah). The AI is the **Patient Educator**. Ask questions about safety, dosage, and side effects. Follow the AI's lead. **{speak_instruction_english}**", # Updated
            'sidebar_title': "🎙️ Simulation Settings",
            'lang_select': "1. Select Language",
            'speed_slider': "2. Speech Speed (1.0 = Normal)",
            'accent_select': "3. Patient Educator Tone/Style", # Updated
            'your_response': "🎤 **Your Patient Question/Concern**", # Updated
            'speak_prompt': "Click to Speak (🎙️)",
            'stop_prompt': "Stop Recording (⏹️)",
            'chat_input_prompt': "Type your patient question or concern here or use the microphone above...", # Updated
            'thinking_spinner': "AI Educator is counselling...", # Updated
            'transcribed_text': "Transcribed Text:",
            'error': "An API error occurred:",
            'accent_options': ["Empathetic & Clear", "Formal & Technical", "Quick & Direct"], # Updated options
            'gemini_model': "gemini-2.5-flash",
            'tts_lang_code': 'en',
            'stt_lang_code': 'en',
            'feedback_button': "Generate AI Educator Self-Assessment Report 📄", # Updated
            'feedback_spinner': "AI is analyzing its counselling performance and generating a structured report...", # Updated
            'feedback_title': f"AI Educator Self-Assessment Report: {PRODUCT_NAME}", # Updated
            'welcome_msg': f"Hello, welcome. I am your Patient Educator. I understand you've been prescribed **{PRODUCT_NAME}** for Nausea and Vomiting of Pregnancy (NVP). Before we start, can you please tell me your name?" # Updated
        }
    else: # Arabic is the default
        return {
            'title': f"محاكاة إرشاد المريض: **الذكاء الاصطناعي كمعلم** لدواء **{PRODUCT_NAME}**", # Updated
            'subheader': "لعب دور المريض لتقييم أداء المعلم", # Updated
            'instructions': f"دورك هو **المريض** (السيدة سارة). الذكاء الاصطناعي هو **مثقف المريض**. اطرح أسئلة حول السلامة والجرعات والآثار الجانبية. اتبع توجيهات الذكاء الاصطناعي. **{speak_instruction_arabic}**", # Updated
            'sidebar_title': "🎙️ إعدادات المحاكاة",
            'lang_select': "1. اختيار اللغة",
            'speed_slider': "2. سرعة الكلام (1.0 = عادي)",
            'accent_select': "3. نمط/نبرة مثقف المريض", # Updated options
            'your_response': "🎤 **سؤال/قلقك كمريض**", # Updated
            'speak_prompt': "انقر للتحدث (🎙️)",
            'stop_prompt': "إيقاف التسجيل (⏹️)",
            'chat_input_prompt': "اكتب سؤالك أو قلقك كمريض هنا أو استخدم الميكروفون أعلاه...", # Updated
            'thinking_spinner': "مثقف المريض (AI) يقدم الإرشاد...", # Updated
            'transcribed_text': "النص المنسوخ:",
            'error': "حدث خطأ أثناء استدعاء API:",
            'accent_options': ["متعاطف وواضح", "رسمي وتقني", "سريع ومباشر"], # Updated options
            'gemini_model': "gemini-2.5-flash",
            'tts_lang_code': 'ar',
            'stt_lang_code': 'ar',
            'feedback_button': "إنشاء تقرير تقييم ذاتي لمثقف المريض (AI) 📄", # Updated
            'feedback_spinner': "الذكاء الاصطناعي يحلل أداءه الإرشادي ويولد التقرير المهيكل...", # Updated
            'feedback_title': f"تقرير التقييم الذاتي لمثقف المريض (AI): {PRODUCT_NAME}", # Updated
            'welcome_msg': f"أهلاً، مرحباً بكِ. أنا مثقف المريض الخاص بكِ. أفهم أنه وُصِفَ لكِ دواء **{PRODUCT_NAME}** لغثيان وقيء الحمل (NVP). قبل أن نبدأ، هل يمكنكِ إخباري باسمكِ؟" # Updated
        }

# --- 3. الشريط الجانبي للتحكم ---

# استخدام متغير لحفظ اللغة المحددة
selected_language = st.sidebar.selectbox(
    "1. اختيار اللغة",
    options=["Arabic", "English"],
    index=1, 
    key='language_selector'
)
texts = get_texts(selected_language)

st.sidebar.title(texts['sidebar_title'])

# التحكم في السرعة والنبرة
tts_speed = st.sidebar.slider(texts['speed_slider'], min_value=0.5, max_value=2.0, value=1.2, step=0.1, key='speed_slider')
selected_accent = st.sidebar.selectbox(texts['accent_select'], options=texts['accent_options'], index=0, key='accent_selector')

# --- إعداد الواجهة (ديناميكي) ---

# استخدام الحاوية الرئيسية للتنظيم
main_container = st.container()

with main_container:
    # Header Section
    st.markdown(f"## {texts['title']}")
    st.subheader(texts['subheader'])

    # Instructions Expander
    with st.expander("Session Instructions", expanded=False):
        st.markdown(texts['instructions'])

# --- 4. المنطق الأساسي: إدارة جلسة الدردشة وتعليمات النظام ---

def get_system_instruction(lang, accent, welcome_msg):
    """
    Generates the system instruction for the Patient Education simulation. 
    The AI acts as the Patient Educator (Counselor), and the user acts as the Patient (Mrs. Sarah).
    """
    
    if lang == 'English':
        educator_persona = f"You are a highly skilled, knowledgeable, and **{accent}** Patient Educator (Counselor). Your role is to counsel the user, who is a non-technical, pregnant patient named Sarah, prescribed {PRODUCT_NAME} for NVP. **Crucially: Respond ONLY in English.**"
        name_capture_prompt = "Thank you, [Patient's Name]. I'm going to explain the key things you need to know about Mornigag, focusing on dosage, safety, and side effects. What is your main concern right now?"
        
    else: # Arabic
        educator_persona = f"أنت مثقف مريض (مستشار) ذو مهارات عالية ومعرفة، ونبرتك/أسلوبك **{accent}**. دورك هو تقديم الإرشاد للمستخدم، وهي مريضة حامل غير تقنية اسمها سارة، وُصِفَ لها {PRODUCT_NAME} لغثيان الحمل. يجب عليك الرد **فقط باللغة العربية** بصفتك مثقف المريض."
        name_capture_prompt = "شكراً لكِ، [Patient's Name]. سأقوم الآن بشرح الأمور الأساسية التي تحتاجين لمعرفتها عن Mornigag، مع التركيز على الجرعة، السلامة، والآثار الجانبية. ما هو قلقكِ الرئيسي في هذه اللحظة؟"
        
    system_instruction = f"""
    You are the **Patient Educator (AI)** in this simulation. The user is the **Pregnant Patient (Mrs. Sarah)**.
    The product being discussed is: {PRODUCT_NAME} (Active Constituents: Doxylamine and Pyridoxine) for Nausea and Vomiting of Pregnancy (NVP).
    
    {educator_persona}

    **CONVERSATION FLOW:**

    1.  **Introduction & Name Capture (AI starts):** You MUST start the conversation by delivering the EXACT welcome message provided below. 
        Message: "{welcome_msg}"
        Wait for the user (Patient) to provide their name (e.g., 'My name is Sarah').
    
    2.  **Acknowledge & Elicit Initial Concern:** Once the Patient provides their name, you MUST acknowledge it and transition them into the counselling session using this exact prompt (using their name): "{name_capture_prompt}".
    
    3.  **Core Counselling & Q&A (AI's role):**
        * **Be Proactive:** Based on the patient's concern (e.g., "safety" or "when to take it"), provide a clear, empathetic, non-technical explanation covering dosage (especially delayed release and nighttime dosing), safety (reassurance about pregnancy use), and common side effects (drowsiness).
        * **Be Reactive:** Respond to all subsequent patient questions (e.g., missed dose, cost, duration of use) with accurate, supportive, and patient-focused information.
        * **Maintain Empathy:** Always acknowledge the patient's anxiety and concerns. Use simple, non-medical terminology.
        * **Keep the Session Focused:** Ensure the conversation stays focused on {PRODUCT_NAME} and the patient's needs.
        
    4.  **Conclusion:** The conversation ends when the Patient (user) indicates they have no further questions (e.g., "I'm done" or "Thank you").
    """
    return system_instruction

# تهيئة تعليمات النظام ديناميكياً
current_system_instruction = get_system_instruction(
    selected_language, 
    selected_accent, 
    texts['welcome_msg']
)

# Key updated to reflect the new roles
current_state_key = f"{selected_language}_{selected_accent}_{PRODUCT_NAME}_Educator_AI" 

if "chat_session" not in st.session_state or st.session_state.get('current_state_key') != current_state_key:
    
    st.session_state.current_state_key = current_state_key
    st.session_state.user_name = None # هذا هو اسم المريض
    
    config = types.GenerateContentConfig(
        system_instruction=current_system_instruction
    )
    
    # بدء جلسة دردشة جديدة
    st.session_state.chat_session = client.chats.create(
        model=texts['gemini_model'], 
        config=config
    )
    
    # تنظيف التقييم عند إعادة التهيئة
    if 'feedback' in st.session_state:
        del st.session_state['feedback']

chat_session = st.session_state.chat_session


# --- وظيفة الحصول على التقييم المهيكل (لأداء مثقف المريض) ---
def get_feedback():
    """Retrieves conversation history and asks the model to provide detailed, structured feedback on its *own* performance as the Educator."""
    history = chat_session.get_history()
    
    # التحقق من وجود محتوى كافٍ (Minimum 3 turns: AI Intro -> User Name -> AI Acknowledge/Ask Concern)
    if len(history) < 3:
        st.session_state['feedback'] = "يجب إكمال مرحلة الترحيب وتبادل الأسماء على الأقل قبل طلب التقييم الذاتي."
        return

    # استخدام الاسم المخزن أو اسم افتراضي
    patient_name = st.session_state.user_name if st.session_state.user_name else "Patient Candidate"

    # تنسيق السجل للحصول على تقرير
    conversation_log = "\n".join([f"Role: {msg.role}\nText: {msg.parts[0].text}\n---" for msg in history if msg.role != 'system'])

    feedback_prompt = f"""
    Analyze the following simulated patient-educator conversation conducted in {selected_language}. You acted as the Patient Educator (Counselor), and the user acted as the Pregnant Patient (Patient Name: {patient_name}) seeking information about {PRODUCT_NAME} for Nausea and Vomiting of Pregnancy (NVP).

    The final output MUST be a structured, single Markdown report written entirely in {selected_language}. Assess your own (the AI Educator's) counselling skills and information delivery against the criteria. Note: Ensure all "Notes for Reviewer" sections are separated by double line breaks (i.e., treated as distinct paragraphs in Markdown).
    
    --- CONVERSATION LOG ---
    {conversation_log}
    --- END CONVERSATION LOG ---

    Generate the report using the following EXACT markdown structure. Fill in the analysis based on the conversation log.

    ## AI Educator Self-Assessment Report: {PRODUCT_NAME} Counselling
    Date: {datetime.date.today().strftime('%Y-%m-%d')}
    Patient Name: {patient_name}

    ### Section 1: Core Medication Education Delivery

    #### Clarity of Purpose & Dosage Explanation
    AI Educator's Explanation: "[Extract the AI Educator's initial explanation of *what* the drug is for and *how* to take it (dosage, timing, adherence tips).]"
    Key Educational Points Covered: [List 3-5 crucial points delivered (e.g., delayed release mechanism, importance of nighttime dosing, NVP indication, consistency).]
    
    **Notes for Reviewer:**
    [Evaluate if the explanation was clear, simple, and non-technical, matching the selected tone ({selected_accent}). Was the critical mechanism/timing emphasized for optimal effect?]

    #### Safety & Side Effect Counselling
    AI Educator's Communication: "[Extract the AI Educator's communication regarding side effects and safety reassurance, based on patient queries.]"
    Key Safety Points Delivered: [List 2-4 critical safety points (e.g., FDA-approved status, high safety profile in pregnancy, most common side effect is drowsiness).]
    
    **Notes for Reviewer:**
    [Evaluate how effectively the AI Educator anticipated and addressed patient fears (e.g., baby safety) and if side effects were explained in a reassuring, balanced manner.]

    ### Section 2: Patient Interaction and Concern Handling

    #### Empathy and Tone Consistency
    AI Educator's Interaction: "[Extract a short segment that demonstrates the AI Educator's tone and empathetic language.]"
    Tone Consistency: [Assess if the AI maintained the requested tone/style ({selected_accent}) throughout the conversation.]
    
    **Notes for Reviewer:**
    [Evaluate the overall demeanor. Was the tone supportive and consistent? Did the AI acknowledge the patient's feelings and use simple language?]

    #### Responsiveness to Patient Questions
    Patient Questions Addressed: "[List 2-3 significant questions/concerns asked by the patient (the user).]"
    AI Educator's Response Quality: [Evaluate the accuracy and practicality of the AI's responses to the patient's questions.]
    
    **Notes for Reviewer:**
    [Assess if all patient questions were directly answered. Was the information provided clinically accurate and easy for a patient to follow?]

    ### Overall Assessment Notes (for human review)

    Communication Style: [Summary sentence on the AI Educator's effectiveness in communicating complex information in a patient-friendly way based on the selected tone.]

    **Strengths identified (Self-Reflection):**
    [List 2-3 major strengths in counselling or communication demonstrated by the AI.]

    **Areas for improvement (Self-Correction):**
    [List 2-3 specific areas where the AI Educator could improve its performance (e.g., "Could have used more analogies," or "Need to pause and check for patient understanding").]
    """
    
    with st.spinner(texts['feedback_spinner']):
        try:
            feedback_response = client.models.generate_content(
                model=texts['gemini_model'],
                contents=feedback_prompt
            )
            st.session_state['feedback'] = feedback_response.text
        except Exception as e:
            st.error(f"{texts['error']} {e}")

# --- 5. تحويل الكلام إلى نص (إدخال المستخدم) ---

# Use a specific container for the input controls to make them visually distinct
input_container = st.container()

with input_container:
    st.markdown("---")
    st.markdown(texts['your_response'])
    
    # Create two columns for controls (mic button) and text input
    col1, col2 = st.columns([1, 4]) 

    with col1:
        # Microphone input
        spoken_text = speech_to_text(
            language=texts['stt_lang_code'],
            start_prompt=texts['speak_prompt'], 
            stop_prompt=texts['stop_prompt'], 
            just_once=True, 
            use_container_width=True,
            key='STT_input_patient' # Changed key to reflect new role
        )

    with col2:
        # Text input 
        written_text = st.text_input(texts['chat_input_prompt'], label_visibility="collapsed", key='chat_input_patient') # Changed key to reflect new role
        
    user_input = spoken_text if spoken_text else written_text

# --- 6. حلقة المحادثة الرئيسية ---

# Use an empty container to hold the chat history, ensuring messages appear sequentially
chat_history_container = st.container()

# Display transcript if speech was detected
if spoken_text:
    chat_history_container.info(f"**{texts['transcribed_text']}** {spoken_text}")

if user_input or not chat_session.get_history():
    
    if user_input:
        
        # منطق التقاط الاسم: 
        if st.session_state.user_name is None:
            # Assuming the first meaningful input after the AI's intro is the patient's name
            name_parts = user_input.split()
            if name_parts:
                st.session_state.user_name = user_input.split()[-1].replace('.', '').replace(',', '')
        
        # عرض رسالة المستخدم (المريض)
        with chat_history_container:
            st.chat_message("user").markdown(format_bidi_text(user_input, selected_language), unsafe_allow_html=True)

        with st.spinner(texts['thinking_spinner']):
            try:
                # إرسال الرسالة والحصول على الرد
                response = chat_session.send_message(user_input)
                ai_response = response.text
                
                # عرض رد الذكاء الاصطناعي (المعلم) مع تنسيق Bidi
                # Changed avatar to reflect the AI is now the Educator/Counsellor
                with chat_history_container:
                    st.chat_message("assistant", avatar="👩‍⚕️").markdown(format_bidi_text(ai_response, selected_language), unsafe_allow_html=True)
                
                # 🗣️ تحويل رد الذكاء الاصطناعي إلى كلام وتشغيله تلقائيًا (TTS)
                tts_key_with_speed = f'tts_key_{texts["tts_lang_code"]}_{str(tts_speed).replace(".", "_")}_educator_ai' 

                text_to_speech(
                    text=ai_response, 
                    language=texts['tts_lang_code'],
                    key=tts_key_with_speed
                )
                
            except Exception as e:
                st.error(f"{texts['error']} {e}")

# عرض جميع الرسائل القديمة (لإعادة بناء الجلسة)
history = chat_session.get_history()
for message in history:
    if message.role != "system":
        display_role = "user" if message.role == "user" else "assistant"
        
        # عرض الرسائل القديمة مع تنسيق Bidi
        if message.role == 'user':
            # User is the Patient
            with chat_history_container:
                st.chat_message(display_role).markdown(format_bidi_text(message.parts[0].text, selected_language), unsafe_allow_html=True)
        elif message.role == 'model':
            # Model is the Educator
            with chat_history_container:
                st.chat_message(display_role, avatar="👩‍⚕️").markdown(format_bidi_text(message.parts[0].text, selected_language), unsafe_allow_html=True)

# --- 7. قسم التقييم ---
st.markdown("---")

# زر التقييم
st.button(texts['feedback_button'], on_click=get_feedback, use_container_width=True)

# عرض التقييم في حالة الجلسة
if 'feedback' in st.session_state:
    with st.expander(texts['feedback_title'], expanded=True):
        st.markdown(st.session_state['feedback'])

# تنظيف التقييم عند إعادة تهيئة الجلسة
if "chat_session" not in st.session_state or st.session_state.get('current_state_key') != current_state_key:
    if 'feedback' in st.session_state:
        del st.session_state['feedback']
    if 'user_name' in st.session_state:
        del st.session_state['user_name']

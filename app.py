import streamlit as st
import base64
from streamlit_mic_recorder import mic_recorder
from groq import Groq
from gtts import gTTS
import io
import json
import re
from datetime import datetime
import pandas as pd
import streamlit.components.v1 as components

# --- 1. PAGE CONFIG & ADVANCED STYLING ---
st.set_page_config(
    page_title="Advanced AI English Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .main-header {
        text-align: center;
        color: #2c3e50;
        font-size: 2.5em;
        margin-bottom: 0.5em;
    }
    .st-emotion-cache-1c7n2ka { max-width: 1200px; margin: auto; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. ADVANCED SIDEBAR SETTINGS ---
with st.sidebar:
    st.markdown('<h1 style="color: white; text-align: center;">⚙️ Advanced Settings</h1>', unsafe_allow_html=True)
    
    # API Key
    GROQ_API_KEY = st.text_input("🔑 Groq API Key", type="password", 
                                 value="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")
    
    if not GROQ_API_KEY:
        st.warning("⚠️ Please enter your Groq API Key to start!")
        st.stop()
    
    client = Groq(api_key=GROQ_API_KEY)
    st.divider()
    
    tutor_style = st.selectbox("👤 Teaching Style", ["Friendly", "Strict", "Professional", "Motivational", "Humorous"])
    accent = st.radio("🌍 English Accent", ["US (American)", "UK (British)", "AU (Australian)", "IN (Indian)"])
    tld_map = {'US (American)': 'com', 'UK (British)': 'co.uk', 'AU (Australian)': 'com.au', 'IN (Indian)': 'com'}
    tld = tld_map.get(accent, 'com')
    
    if "user_level" not in st.session_state:
        st.session_state.user_level = "Beginner"
    
    level = st.selectbox("📈 Your Level", ["Beginner", "Intermediate", "Advanced"], 
                         index=["Beginner", "Intermediate", "Advanced"].index(st.session_state.user_level))
    st.session_state.user_level = level
    
    model = st.selectbox("🤖 AI Model", ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"])
    enable_voice = st.checkbox("🔊 Enable Tutor Voice", value=True)
    enable_vocabulary_tracker = st.checkbox("📚 Vocabulary Tracker", value=True)

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "progress" not in st.session_state:
    st.session_state.progress = {"sessions": 1, "total_words": 0, "vocabulary": [], "idioms_learned": []}

# --- 4. FUNCTIONS ---
def auto_scroll():
    components.html("""<script>window.parent.document.querySelector('.stAppViewContainer').scrollTop = 99999;</script>""", height=0)

# --- 5. UI LAYOUT ---
st.markdown('<h2 class="main-header">🎓 AI English Tutor</h2>', unsafe_allow_html=True)

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
        st.caption(f"🕒 {message.get('timestamp', '')}")
        st.markdown(message["content"])

# --- 6. RECORDING & LOGIC ---
st.markdown("---")
cols = st.columns([1, 2, 1])
with cols[1]:
    audio_info = mic_recorder(start_prompt="🗣️ Tap to Speak", stop_prompt="🔄 Processing...", just_once=True, use_container_width=True, key='recorder')

if audio_info:
    try:
        # Step 1: Transcription
        audio_file = ("input.wav", audio_info['bytes'], "audio/wav")
        transcription = client.audio.transcriptions.create(file=audio_file, model="whisper-large-v3-turbo", language="en")
        user_text = transcription.text.strip()
        
        if user_text:
            # Update State
            timestamp = datetime.now().strftime("%H:%M")
            st.session_state.messages.append({"role": "user", "content": user_text, "timestamp": timestamp})
            st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")

# Handle generating AI Response after a user message is added
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.spinner("Tutor is thinking..."):
        # System Prompt Setup
        STYLE_PROMPTS = {
            "Friendly": "Be warm and encouraging 😊", "Strict": "Be direct with corrections.",
            "Professional": "Use formal English.", "Motivational": "Inspire the user!", "Humorous": "Use puns."
        }
        
        SYSTEM_PROMPT = f"""You are an English Tutor. Style: {STYLE_PROMPTS[tutor_style]}. Level: {st.session_state.user_level}.
        1. Correct errors. 2. Reply naturally. 3. Introduce 1 new word or idiom in this format: [VOCAB: word|meaning|example].
        Keep responses under 4 sentences."""

        chat_history = [{"role": "system", "content": SYSTEM_PROMPT}] + \
                       [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]

        # Step 2: Call Groq API (THIS WAS MISSING)
        response = client.chat.completions.create(model=model, messages=chat_history)
        ai_response = response.choices[0].message.content
        
        # Step 3: Process Metadata (Vocab tracker)
        vocab_match = re.search(r"\[VOCAB: (.*?)\]", ai_response)
        if vocab_match and enable_vocabulary_tracker:
            parts = vocab_match.group(1).split('|')
            if len(parts) == 3:
                st.session_state.progress["vocabulary"].append({"Word": parts[0], "Meaning": parts[1], "Example": parts[2]})

        # Add to history
        st.session_state.messages.append({"role": "assistant", "content": ai_response, "timestamp": datetime.now().strftime("%H:%M")})
        
        # Step 4: Voice Synthesis
        if enable_voice:
            clean_text = re.sub(r"\[.*?\]", "", ai_response) # Remove tags for audio
            tts = gTTS(text=clean_text, lang='en', tld=tld)
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            st.audio(audio_fp, format="audio/mp3", autoplay=True)
            
        st.rerun()

# --- 7. TRACKERS ---
if enable_vocabulary_tracker and st.session_state.progress["vocabulary"]:
    with st.expander("📚 Your Vocabulary Bank"):
        st.table(pd.DataFrame(st.session_state.progress["vocabulary"]))

auto_scroll()
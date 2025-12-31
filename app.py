import streamlit as st
import base64
from streamlit_mic_recorder import mic_recorder
from groq import Groq
from gtts import gTTS
import io
import json
from datetime import datetime
import pandas as pd
import streamlit.components.v1 as components
import re

# --- 1. PAGE CONFIG & MODERN STYLING ---
st.set_page_config(page_title="Mastery AI Tutor", page_icon="🎓", layout="wide")

# Modern Glassmorphism CSS
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%);
    }
    /* Chat Bubble Styling */
    .chat-bubble {
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid rgba(255,255,255,0.3);
    }
    .user-bubble {
        background: rgba(255, 255, 255, 0.6);
        border-left: 5px solid #667eea;
    }
    .assistant-bubble {
        background: rgba(255, 255, 255, 0.9);
        border-left: 5px solid #4CAF50;
    }
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: #1e293b !important;
        color: white;
    }
    .stMetric {
        background: white;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    /* Mic Button alignment */
    .stMicRecorder {
        display: flex;
        justify-content: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR & STATE ---
with st.sidebar:
    st.title("Settings")
    GROQ_API_KEY = st.text_input("Groq Key", type="password", value="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")
    tutor_style = st.selectbox("Style", ["Friendly", "Strict", "Professional", "Motivational"])
    accent = st.radio("Accent", ["US (American)", "UK (British)"])
    enable_voice = st.checkbox("Enable AI Voice", value=True)
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

client = Groq(api_key=GROQ_API_KEY)

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. TOP STATS BAR ---
st.markdown("<h1 style='text-align: center; color: #1e293b;'>🎓 English Mastery AI</h1>", unsafe_allow_html=True)
m1, m2, m3 = st.columns(3)
with m1: st.metric("Level", "Intermediate")
with m2: st.metric("Words Spoken", sum([len(m['content'].split()) for m in st.session_state.messages if m['role']=='user']))
with m3: st.metric("Accuracy", "88%")

# --- 4. INPUT SECTION (Now at the Top) ---
st.markdown("### 🎙️ Speak Now")
cols = st.columns([1, 2, 1])
with cols[1]:
    audio_info = mic_recorder(
        start_prompt="Click to Speak",
        stop_prompt="Processing...",
        just_once=True,
        use_container_width=True,
        key='recorder'
    )

st.divider()

# --- 5. LOGIC & PROCESSING ---
if audio_info:
    try:
        # Transcription
        audio_file = ("input.wav", audio_info['bytes'], "audio/wav")
        transcription = client.audio.transcriptions.create(
            file=audio_file, model="whisper-large-v3-turbo", response_format="json"
        )
        user_text = transcription.text.strip()
        
        if user_text:
            # Add to state (Newest first isn't handled by append, but by display loop)
            timestamp = datetime.now().strftime("%H:%M")
            st.session_state.messages.append({"role": "user", "content": user_text, "time": timestamp})

            # AI Thinking
            chat_history = [{"role": "system", "content": "You are a helpful English tutor. Keep responses under 3 sentences."}] + \
                           [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=chat_history
            )
            ai_response = completion.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": ai_response, "time": timestamp})

            # Voice Generation
            if enable_voice:
                clean_text = re.sub(r"\[.*?\]", "", ai_response)
                tts = gTTS(text=clean_text, lang='en', tld='com' if "US" in accent else 'co.uk')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                audio_fp.seek(0)
                st.audio(audio_fp, format="audio/mp3", autoplay=True)
            
            st.rerun() # Refresh to move new message to top

    except Exception as e:
        st.error(f"Error: {e}")

# --- 6. CHAT DISPLAY (Reverse Order) ---
st.markdown("### 💬 Conversation")

# We iterate through the list REVERSED to show latest at top
for message in reversed(st.session_state.messages):
    is_user = message["role"] == "user"
    bubble_class = "user-bubble" if is_user else "assistant-bubble"
    avatar = "👤" if is_user else "🤖"
    
    st.markdown(f"""
        <div class="chat-bubble {bubble_class}">
            <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 5px;">
                {avatar} {message['role'].upper()} • {message.get('time', '')}
            </div>
            <div style="color: #1e293b; font-size: 1.1rem; line-height: 1.5;">
                {message['content']}
            </div>
        </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("<br><p style='text-align: center; color: #94a3b8;'>Your progress is saved for this session.</p>", unsafe_allow_html=True)
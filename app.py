import streamlit as st
from streamlit_mic_recorder import mic_recorder
from groq import Groq
from gtts import gTTS
import io
import json
import time
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional
import streamlit.components.v1 as components

# --- 1. PAGE CONFIG & ADVANCED STYLING ---
st.set_page_config(
    page_title="Advanced AI English Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern, responsive design
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
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .st-emotion-cache-1c7n2ka { max-width: 1200px; margin: auto; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 0 10px 10px 0;
    }
    .sidebar .stSelectbox > label { color: white; font-weight: bold; }
    .sidebar .stRadio > label { color: white; }
    .metric-card { background: white; padding: 1rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .progress-bar { height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; }
    .progress-fill { height: 100%; background: linear-gradient(90deg, #4CAF50, #45a049); transition: width 0.3s ease; }
    .audio-container { width: 100%; margin: 10px 0; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ADVANCED SIDEBAR SETTINGS ---
with st.sidebar:
    st.markdown('<h1 style="color: white; text-align: center;">⚙️ Advanced Settings</h1>', unsafe_allow_html=True)
    
    # API Key with secure input
    GROQ_API_KEY = st.text_input("🔑 Groq API Key", type="password",
                                 help="Get your key from groq.com",
                                 value="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")
    
    if not GROQ_API_KEY:
        st.warning("⚠️ Please enter your Groq API Key to start!")
        st.stop()
    
    client = Groq(api_key=GROQ_API_KEY)
    
    st.divider()
    
    # Enhanced tutor options
    tutor_style = st.selectbox("👤 Teaching Style",
                               ["Friendly", "Strict", "Professional", "Motivational", "Humorous"],
                               index=0,
                               help="Choose how the tutor interacts with you.")
    
    accent = st.radio("🌍 English Accent",
                      ["US (American)", "UK (British)", "AU (Australian)", "IN (Indian)"],
                      index=0,
                      help="Select the accent for TTS.")
    tld_map = {'US (American)': 'com', 'UK (British)': 'co.uk', 'AU (Australian)': 'com.au', 'IN (Indian)': 'com'}
    tld = tld_map.get(accent, 'com')
    
    # User level with persistence
    if "user_level" not in st.session_state:
        st.session_state.user_level = "Beginner"
    
    level = st.selectbox("📈 Your Current Level",
                         ["Beginner", "Intermediate", "Advanced"],
                         index=["Beginner", "Intermediate", "Advanced"].index(st.session_state.user_level),
                         help="This adapts the difficulty.")
    st.session_state.user_level = level
    
    # Model selection
    model = st.selectbox("🤖 AI Model",
                         ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"],
                         index=0,
                         help="Choose the Groq model for responses.")
    
    # Enable/disable features
    enable_vocabulary_tracker = st.checkbox("📚 Vocabulary Tracker", value=True)
    enable_progress_chart = st.checkbox("📊 Progress Chart", value=True)
    
    st.divider()
    st.markdown("### 🔗 Share & Export")
    share_url = st.text_input("Share Link", value=f"https://share.streamlit.io/your-app-url", disabled=True)
    if st.button("📤 Export Chat History"):
        chat_json = json.dumps(st.session_state.messages, indent=2)
        st.download_button("Download JSON", chat_json, "chat_history.json", "application/json")

# --- 3. ENHANCED SESSION STATE ---
@st.cache_data(ttl=3600) # Cache for 1 hour
def load_progress():
    return {
        "sessions": 0,
        "total_words": 0,
        "corrections_made": 0,
        "last_session": None,
        "vocabulary": [],
        "achievements": [],
        "grammar_tips": [],
        "idioms_learned": [],
        "pronunciation_notes": []
    }

if "messages" not in st.session_state:
    st.session_state.messages = []
if "progress" not in st.session_state:
    st.session_state.progress = load_progress()

# Update progress on new session
if not st.session_state.progress["last_session"] or (datetime.now() - st.session_state.progress["last_session"]).days > 1:
    st.session_state.progress["sessions"] += 1
    st.session_state.progress["last_session"] = datetime.now()

# --- 4. MAIN INTERFACE WITH METRICS ---
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    st.markdown('<h2 class="main-header">🎓 AI English Tutor</h2>', unsafe_allow_html=True)
    st.caption(f"👤 Style: **{tutor_style}** | 📈 Level: **{st.session_state.user_level}**")

with col3:
    # Progress Metrics
    col31, col32 = st.columns(2)
    with col31:
        st.metric("Sessions", st.session_state.progress["sessions"])
    with col32:
        fluency_score = min(100, st.session_state.progress["sessions"] * 10 + len(st.session_state.progress["vocabulary"]))
        st.metric("Fluency %", fluency_score, delta=5 if fluency_score > 50 else 0)

# Display chat history with timestamps
st.subheader("💬 Conversation History")
for i, message in enumerate(st.session_state.messages):
    timestamp = message.get("timestamp", datetime.now().strftime("%H:%M"))
    with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
        st.caption(f"🕒 {timestamp}")
        st.markdown(message["content"])
        
        # Highlight corrections in AI responses
        if message["role"] == "assistant" and "Correction:" in message["content"]:
            st.markdown("**🔍 Correction Highlighted**")

# Enhanced Trackers
if enable_vocabulary_tracker:
    if st.session_state.progress["vocabulary"]:
        st.subheader("📚 Vocabulary Learned")
        vocab_df = pd.DataFrame(st.session_state.progress["vocabulary"], columns=["Word", "Meaning", "Example"])
        st.dataframe(vocab_df, use_container_width=True, hide_index=True)
    
    if st.session_state.progress["idioms_learned"]:
        st.subheader("🗣️ Idioms & Phrases")
        idioms_df = pd.DataFrame(st.session_state.progress["idioms_learned"], columns=["Idiom", "Meaning", "Usage"])
        st.dataframe(idioms_df, use_container_width=True, hide_index=True)

if enable_progress_chart and st.session_state.progress["sessions"] > 1:
    st.subheader("📊 Progress Over Time")
    chart_data = {
        "type": "line",
        "data": {
            "labels": [f"Session {i+1}" for i in range(st.session_state.progress["sessions"])],
            "datasets": [{
                "label": "Fluency Score",
                "data": [min(100, i * 10 + j * 2) for i, j in enumerate(range(st.session_state.progress["sessions"]))], # Simulated progress
                "borderColor": "#4CAF50",
                "backgroundColor": "rgba(76, 175, 80, 0.2)",
                "fill": True
            }]
        },
        "options": {
            "responsive": True,
            "scales": {"y": {"beginAtZero": True, "max": 100}}
        }
    }
    components.html(f"""
    <canvas id="progressChart" width="400" height="200"></canvas>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        const ctx = document.getElementById('progressChart').getContext('2d');
        new Chart(ctx, {chart_data});
    </script>
    """.replace("{chart_data}", json.dumps(chart_data)), height=300)

# --- 5. ADVANCED MIC RECORDER WITH FEEDBACK ---
st.markdown("---")
st.subheader("🎙️ Start Speaking! (Tap the Mic Below)")
cols = st.columns([1, 3, 1])
with cols[1]:
    audio_info = mic_recorder(
        start_prompt="🗣️ Tap to Record Your English",
        stop_prompt="🔄 Transcribing & Responding...",
        just_once=True,
        use_container_width=True,
        key='advanced_recorder'
    )

# --- 6. ENHANCED LOGIC WITH COMPREHENSIVE LEARNING TRACKING ---
if audio_info:
    try:
        # STEP 1: Advanced Transcription with Language Detection
        audio_file = ("input.wav", audio_info['bytes'], "audio/wav")
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3-turbo",
            response_format="json",
            language="en" # Force English detection
        )
        user_text = transcription.text.strip()
        
        if not user_text:
            st.warning("😶 No speech detected. Please try again!")
            st.stop()
        
        # Add timestamp
        user_message = {"role": "user", "content": user_text, "timestamp": datetime.now().strftime("%H:%M")}
        with st.chat_message("user"):
            st.markdown(user_text)
        st.session_state.messages.append(user_message)
        
        # Update progress: Count words
        word_count = len(user_text.split())
        st.session_state.progress["total_words"] += word_count
        
        # STEP 2: Comprehensive All-in-One System Prompt
        STYLE_ADAPTATIONS = {
            "Friendly": "Be warm, encouraging, and use emojis occasionally. 😊",
            "Strict": "Be direct with corrections, but supportive. No sugarcoating errors.",
            "Professional": "Use formal language, focus on precision and clarity.",
            "Motivational": "Inspire confidence! End with empowering questions.",
            "Humorous": "Add light-hearted jokes or puns related to English learning."
        }
        
        LEVEL_ADAPTATIONS = {
            "Beginner": "Use simple sentences. Focus on basics: vocabulary, simple grammar, articles/prepositions. Introduce 1 easy word + basic pronunciation tip.",
            "Intermediate": "Build on mid-level structures. Introduce 1 idiom/phrasal verb + grammar nuance (tenses/conditionals). Include cultural note.",
            "Advanced": "Dive into nuances, idioms, cultural references. Challenge with synonyms, debate prompts, advanced pronunciation (intonation/stress). Suggest reading/listening resources."
        }
        
        SYSTEM_PROMPT = f"""
        ### IDENTITY & TOP-LEVEL GOAL
        You are the Ultimate Adaptive English Mastery Coach – a single, all-encompassing guide to fluent, native-like English. Your mission: Transform the user holistically across ALL pillars of language learning in every interaction: Speaking (fluency/pronunciation), Listening (via response modeling), Reading/Writing (implicit through examples), Grammar/Vocab/Idioms, Cultural Nuances, and Confidence-Building. Adapt dynamically to {st.session_state.user_level} using i+1 (introduce concepts 10% beyond their current grasp). Track progress across sessions for personalized evolution.
        ### STYLE INTEGRATION: {STYLE_ADAPTATIONS[tutor_style]}
        
        ### LEVEL-SPECIFIC FOCUS: {LEVEL_ADAPTATIONS[st.session_state.user_level]}
        
        ### CORE PEDAGOGY: 7-STEP ALL-IN-ONE LEARNING CYCLE (Ultra-Concise: 4 Sentences Max Total)
        Respond in a seamless, natural flow blending these steps – no rigid numbering unless correcting. Prioritize immersion over lists.
        1. **ERROR SCAN & CORRECTION**: Detect grammar (tenses/articles/prepositions), vocab choice, phrasing, or pronunciation hints (e.g., "Stress 'im-POR-tant' for emphasis"). If error: "Quick fix: [Natural rephrase]. (Why? [1-phrase ESL tip])". Skip if flawless.
        2. **CONTENT ENGAGEMENT**: Mirror & encourage their idea (e.g., "That's a fun story – reminds me of...").
        3. **VOCAB/IDOM EXPANSION**: Weave in 1 targeted element: "Swap in 'exhilarated' (thrilled + energized) – like when you nailed that presentation!".
        4. **GRAMMAR DEEP-DIVE**: If relevant, slip in a micro-lesson: "Notice how 'would have' adds that hypothetical vibe?".
        5. **PRONUNCIATION/CULTURAL TIP**: Add a quick audio-friendly note: "Say it with rising intonation for questions – Brits love that polite lift!".
        6. **SKILLS CROSS-TRAIN**: Suggest a mini-extension: "Try describing it in past perfect next" or "Listen to a podcast on this topic for real accents".
        7. **MOMENTUM HOOK**: Always propel forward with an open, thematic question: "How'd that feel? What's your wildest travel tale?".
        
        ### GLOBAL GUIDELINES FOR HOLISTIC LEARNING
        - **IMMERSIVE & NATURAL**: Contractions (I'm, gonna), varied sentence lengths for rhythm. Mirror user's energy/tone.
        - **BALANCED COVERAGE**: Rotate focus across pillars (e.g., vocab one turn, grammar next) to "learn everything" without overload.
        - **PROGRESS TRACKING**: Tag new elements: [VOCAB: word|meaning|example], [IDIOM: phrase|meaning|usage], [GRAMMAR: rule|example], [PRONUN: tip|phonetic], [CULTURE: note|context], [ACHIEVE: milestone|reward].
        - **CONCISE YET RICH**: Under 4 sentences. End strong to spark reply.
        - **INSPIRATIONAL ARC**: Build user's confidence – every response advances them toward "top-level" fluency.
        """
        
        chat_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + \
                        [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages[-10:]] # Last 10 for context
        
        # STEP 3: Generate Response
        with st.spinner("🤔 AI is thinking..."):
            completion = client.chat.completions.create(
                model=model,
                messages=chat_messages,
                temperature=0.7 if tutor_style in ["Friendly", "Humorous"] else 0.5,
                max_tokens=300 # Slightly more for richer content
            )
            ai_response = completion.choices[0].message.content
        
        # Enhanced Parsing for All Trackers
        tags = {
            "VOCAB": ("vocabulary", lambda parts: {"Word": parts[0].strip(), "Meaning": parts[1].strip(), "Example": parts[2].strip()}),
            "IDIOM": ("idioms_learned", lambda parts: {"Idiom": parts[0].strip(), "Meaning": parts[1].strip(), "Usage": parts[2].strip()}),
            "GRAMMAR": ("grammar_tips", lambda parts: {"Rule": parts[0].strip(), "Example": " | ".join(parts[1:]).strip()}),
            "PRONUN": ("pronunciation_notes", lambda parts: {"Tip": " | ".join(parts).strip()}),
            "CULTURE": ("grammar_tips", lambda parts: {"Cultural Note": " | ".join(parts).strip()}), # Reuse for simplicity
            "ACHIEVE": ("achievements", lambda parts: [" | ".join(parts).strip()])
        }
        
        for tag, (key, parser) in tags.items():
            if f"[{tag}:" in ai_response:
                matches = [m.split("]")[0].split("|") for m in ai_response.split(f"[{tag}:") if "|" in m and "]" in m]
                for match in matches:
                    if len(match) >= 2:
                        item = parser(match)
                        if isinstance(st.session_state.progress[key], list):
                            st.session_state.progress[key].append(item)
                        st.session_state.progress["corrections_made"] += 1 if tag == "ACHIEVE" else 0
        
        # Display AI Response (Textual reply - kept as is)
        ai_message = {"role": "assistant", "content": ai_response, "timestamp": datetime.now().strftime("%H:%M")}
        with st.chat_message("assistant"):
            st.markdown(ai_response)
        st.session_state.messages.append(ai_message)
        
        # STEP 4: Advanced TTS with Speed Control - UPGRADED FOR RELIABLE VOICE PLAYBACK
        speed = 1.0 if st.session_state.user_level == "Beginner" else 1.2 # Slower for beginners
        tts = gTTS(text=ai_response, lang='en', tld=tld, slow=(speed < 1.0))
        
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        
        # Encode audio to base64 for HTML embedding (more reliable autoplay)
        audio_base64 = base64.b64encode(audio_fp.read()).decode('utf-8')
        
        # Play Audio Immediately with HTML5 Audio (Better autoplay support after user mic interaction)
        components.html(f"""
        <div class="audio-container">
            <audio controls autoplay style="width: 100%;">
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                Your browser does not support the audio element.
            </audio>
            <p style="text-align: center; color: #666; font-size: 0.9em;">🔊 Tutor Speaking... (Voice response active!)</p>
        </div>
        """, height=80)
        
        # Feedback Toast
        st.success(f"✅ Response ready! Words spoken: {word_count} | Fluency: {fluency_score}% | New Learnings: {len(st.session_state.progress.get('vocabulary', [])) + len(st.session_state.progress.get('idioms_learned', []))} unlocked!")
        
        # Estimate audio duration (~150 words per minute, adjust for speed) and delay rerun to let voice finish
        estimated_duration = (len(ai_response.split()) / 150) * 60 / speed  # Seconds
        time.sleep(max(3, estimated_duration))  # Min 3s delay, or estimated time
        
        # Auto-scroll to bottom (After TTS delay to avoid interrupting playback)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Oops! Error: {str(e)}. Check API key or connection.")
        if "unauthorized" in str(e).lower():
            st.warning("🔑 Invalid API key – please update in sidebar.")

# --- 7. FOOTER WITH TIPS ---
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d;'>
    💡 **Pro Tip**: Speak freely – the AI covers EVERY aspect of English in one seamless flow! Voice responses now play reliably like a real tutor.
    <br> Built with ❤️ using Streamlit & Groq. Share your mastery journey!
</div>
""", unsafe_allow_html=True)
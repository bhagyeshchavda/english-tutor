import streamlit as st
from streamlit_mic_recorder import mic_recorder
from groq import Groq
from gtts import gTTS
import io

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="English Tutor AI", page_icon="🎙️", layout="centered")

# Custom CSS for a cleaner Mobile look
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .st-emotion-cache-1c7n2ka { max-width: 700px; margin: auto; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #ddd; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR SETTINGS ---
with st.sidebar:
    st.title("⚙️ Tutor Settings")
    GROQ_API_KEY = st.text_input("Enter Groq API Key", type="password", value="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")
    client = Groq(api_key=GROQ_API_KEY)
    
    st.divider()
    tutor_style = st.selectbox("Teaching Style", ["Friendly", "Strict", "Professional"])
    accent = st.radio("English Accent", ["US (American)", "UK (British)"], index=0)
    tld = 'com' if "US" in accent else 'co.uk'

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. MAIN INTERFACE ---
st.title("🎙️ AI English Tutor")
st.caption(f"Currently in **{tutor_style}** mode. Speak to start learning!")

# Display chat history in bubbles
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. THE MIC (The Floating Control) ---
st.write("---")
cols = st.columns([1, 2, 1])
with cols[1]:
    audio_info = mic_recorder(
        start_prompt="Tap to Speak",
        stop_prompt="Processing...",
        just_once=True,
        use_container_width=True,
        key='recorder'
    )

# --- 6. LOGIC ---
if audio_info:
    try:
        # STEP 1: Transcription
        audio_file = ("sample.wav", audio_info['bytes'], "audio/wav")
        user_text = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3-turbo",
            response_format="text"
        )
        
        # Display User Message
        with st.chat_message("user"):
            st.markdown(user_text)
        st.session_state.messages.append({"role": "user", "content": user_text})

        # STEP 2: Thinking
        SYSTEM_PROMPT = """
            ### IDENTITY
            You are an expert "Adaptive English Language Coach." Your goal is to move the user from their current level (Beginner/Intermediate) toward native-like fluency through natural conversation.

            ### CORE PEDAGOGY: THE 4-STEP RESPONSE
            For every user input, your response must follow this sequence:
            1. CORRECTION: If the user made a mistake (grammar, word choice, or awkward phrasing), start with: "Correction: [Natural version of their sentence]". Briefly explain why (e.g., "We use 'since' for a point in time"). If no mistake, skip this.
            2. ENCOURAGEMENT: Give a very brief, friendly reaction to their content (e.g., "That sounds like a great weekend!").
            3. THE CHALLENGE: Introduce ONE new "Level-Up" element. 
               - If user is Beginner: Suggest a slightly better word.
               - If user is Intermediate: Introduce a common idiom or phrasal verb related to the topic.
               - If user is Advanced: Challenge their nuance or formal vs. informal tone.
            4. THE HOOK: Always end with an open-ended question to keep them speaking.

            ### STYLE GUIDELINES
            - ADAPTIVE LEVEL: Listen to the user's complexity. Speak at a level just 10% harder than theirs (i.e., use the 'i+1' theory of language acquisition).
            - CONCISE: Keep your total response under 3 sentences (to prevent the user from being overwhelmed).
            - NATURAL: Use modern, spoken contractions (I'm, don't, gonna) unless teaching formal English.
            - FOCUS: Prioritize corrections on common "ESL" errors like articles (a/an/the), prepositions, and verb tenses.
            """
        chat_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=chat_messages
        )
        ai_response = completion.choices[0].message.content

        # Display AI Message
        with st.chat_message("assistant"):
            st.markdown(ai_response)
        st.session_state.messages.append({"role": "assistant", "content": ai_response})

        # STEP 3: Voice
        tts = gTTS(text=ai_response, lang='en', tld=tld)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        st.audio(audio_fp, format="audio/mp3", autoplay=True)

    except Exception as e:
        st.error(f"Please check your API Key: {e}")
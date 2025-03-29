import streamlit as st
import json
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image
import pytesseract
import time  # Simulate loading effect

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"

# Load environment variables
load_dotenv()

# Configure Google Gemini AI API Key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def extract_text_from_image(image):
    return pytesseract.image_to_string(image).strip()

def fetch_questions(text_content, quiz_level):
    RESPONSE_JSON = {
        "mcqs": [
            {
                "mcq": "multiple choice question1",
                "options": {
                    "a": "choice here1",
                    "b": "choice here2",
                    "c": "choice here3",
                    "d": "choice here4",
                },
                "correct": "correct choice option",
            }
        ]
    }

    PROMPT_TEMPLATE = """ 
    Text: {text_content}
    You are an expert in generating MCQ-type quizzes based on the provided content.
    Given the above text, create a quiz of 10 multiple-choice questions, keeping the difficulty level as {quiz_level}.
    Ensure to format your response like RESPONSE_JSON below.
    Here is the RESPONSE_JSON:
    {RESPONSE_JSON}
    """
    
    formatted_template = PROMPT_TEMPLATE.format(
        text_content=text_content, quiz_level=quiz_level, RESPONSE_JSON=json.dumps(RESPONSE_JSON)
    )

    try:
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        response = model.generate_content(formatted_template)
        extracted_response = response.text.strip().strip("```json").strip("```")
        
        return json.loads(extracted_response).get("mcqs", []) if response else []
    except:
        return []


def reset_quiz():
    """ Reset quiz state and return to home page without clearing extracted text and image """
    st.session_state.quiz_generated = False  # Mark quiz as not generated
    st.session_state.loading = False  # Reset loading state
    st.session_state.questions = []  # Clear quiz questions
    st.session_state.selected_options = {}  # Clear selected answers
    st.rerun()  # Force rerun the app

    



def main():
    st.set_page_config(page_title="Quiz Generator", layout="wide")

    # Custom CSS styles
    st.markdown("""
        <style>
            body { font-family: 'Arial', sans-serif; }
            .stButton>button { background-color: #ff5722; color: white; font-size: 18px; padding: 10px 20px; border-radius: 10px; border: none; transition: 0.3s; }
            .stButton>button:hover { background-color: #e64a19; }
            .quiz-container { background-color: #1e1e1e; color: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(255, 255, 255, 0.2); text-align: center; }
            .loading-screen { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: black; display: flex; justify-content: center; align-items: center; color: white; font-size: 30px; font-weight: bold; animation: fadeIn 1s; }
            @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        </style>
    """, unsafe_allow_html=True)

    st.title("📚 AI-Powered Quiz Generator")

    # Initialize session states
    if "questions" not in st.session_state:
        st.session_state.questions = []
    if "selected_options" not in st.session_state:
        st.session_state.selected_options = {}
    if "quiz_generated" not in st.session_state:
        st.session_state.quiz_generated = False
    if "uploaded_image" not in st.session_state:
        st.session_state.uploaded_image = None
    if "extracted_text" not in st.session_state:
        st.session_state.extracted_text = ""
    if "loading" not in st.session_state:
        st.session_state.loading = False
        
    


    if not st.session_state.quiz_generated and not st.session_state.loading:
        option = st.radio("📌 Choose Input Method:", ("Text Input", "Image Upload"))

        if option == "Text Input":
            st.session_state.extracted_text = st.text_area("✏️ Paste the text content here:")

        elif option == "Image Upload":
            uploaded_image = st.file_uploader("📷 Upload an Image", type=["png", "jpg", "jpeg"])
            if uploaded_image:
                st.session_state.uploaded_image = uploaded_image
                image = Image.open(uploaded_image)
                st.session_state.extracted_text = extract_text_from_image(image)
                st.text_area("📝 Extracted Text:", st.session_state.extracted_text, height=150)

    quiz_level = st.selectbox("🎯 Select Quiz Level:", ["Easy", "Medium", "Hard"])

    if st.button("🚀 Generate Quiz"):
        if st.session_state.extracted_text.strip():
            st.session_state.loading = True
            st.rerun()

    if st.session_state.loading:
        st.markdown('<div class="loading-screen">🚀 Generating Quiz... Please Wait ⏳</div>', unsafe_allow_html=True)
        time.sleep(3)  # Simulate loading
        st.session_state.questions = fetch_questions(st.session_state.extracted_text, quiz_level.lower())
        st.session_state.quiz_generated = True
        st.session_state.loading = False
        st.rerun()

    if st.session_state.quiz_generated:
        st.markdown('<div class="quiz-container">', unsafe_allow_html=True)
        st.header("🎯 Quiz Questions")

        for i, question in enumerate(st.session_state.questions):
            st.subheader(f"Q{i+1}: {question['mcq']}")
            options = question["options"]
            key = f"q{i}"

            selected_option = st.radio(
                f"Select an answer for Q{i+1}:",
                list(options.values()),
                key=key,
                index=None
            )

            st.session_state.selected_options[key] = selected_option

        if st.button("✅ Submit Quiz"):
            marks = 0
            st.header("🏆 Quiz Results:")

            for i, question in enumerate(st.session_state.questions):
                st.subheader(f"🔹 {question['mcq']}")
                selected = st.session_state.selected_options.get(f"q{i}", None)
                correct_answer = question["options"][question["correct"]]

                if selected:
                    st.write(f"🟢 Your answer: {selected}")
                else:
                    st.write("⚠️ You did not select an answer.")

                st.write(f"✅ Correct answer: {correct_answer}")

                if selected == correct_answer:
                    marks += 1

            st.subheader(f"🎉 You scored {marks} out of {len(st.session_state.questions)}")

            # "Back to Home" Button
            if st.button("🏠 Back to Home"):
                 # Reset quiz-related states
                st.session_state.quiz_generated = False  # Ensure quiz is marked as not generated
                st.session_state.questions = []  # Clear quiz questions
                st.session_state.selected_options = {}  # Clear selected answers
                st.session_state.loading = False  # Reset loading state
                st.session_state.page = "home"  # Set the state to home page
                st.rerun()  # Force rerun to reflect changes
                

        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

import streamlit as st
import google.generativeai as genai
import os
import hashlib
import re
import random
import string
import json
from dotenv import load_dotenv
import time

load_dotenv()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_info" not in st.session_state:
    st.session_state["user_info"] = None
if "previous_questions" not in st.session_state:
    st.session_state["previous_questions"] = []

st.set_page_config(page_title="TalentScout-An AI Hiring Assistant", layout="wide",initial_sidebar_state="auto",
    menu_items={
        'Get Help': 'https://github.com/prasanna1256/',
        'Report a bug': "https://github.com/prasanna1256/",
        'About': "# TalentScout: An AI Hiring Assistant (Powered by Gemini)"
      })

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
JSON_FILE_PATH = "data.json"

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

SYSTEM_PROMPT = """You are TalentScout, a friendly and professional technical hiring assistant AI.
Your primary purpose is to conduct initial technical screenings for job candidates.

Follow these steps precisely:
1.  **Start:** Greet the candidate warmly ONCE at the beginning of the conversation. Briefly explain your role (AI hiring assistant conducting an initial screening) and the process (collecting info, asking technical questions). Mention they can type "exit" or "quit" to end the session. Do NOT repeat the full greeting and explanation after the conversation starts.
2.  **Gather Info:** Politely ask for the following details, one by one, waiting for a response after each question:
    * Full Name
    * Email Address
    * Phone Number
    * Years of Professional Experience (as a number)
    * Desired Position(s)
    * Current Location (City, Country)
    * Tech Stack: Ask them to list their main programming languages, frameworks, databases, and tools, separated by commas.
3.  **Generate & Ask Questions:** ONLY after successfully gathering the tech stack, analyze it. Generate 3-5 relevant technical questions *specifically tailored* to the listed technologies. Ask these technical questions one at a time, waiting for the candidate's answer before asking the next.
4.  **Conversation Flow:** Maintain the context of the conversation. If the user provides information before you ask for it, acknowledge it and move to the next required piece of information. If input is unclear (e.g., for years of experience), politely ask for clarification. Stay focused ONLY on the screening process (info gathering and technical questions). Do not engage in off-topic discussions.
5.  **Ending:** If the user types "exit", "quit", or similar keywords at any point, OR after you have finished asking all the generated technical questions, thank them sincerely for their time, inform them their information has been recorded and someone from the hiring team will be in touch about the next steps, and say goodbye professionally.
6.  **Tone:** Be conversational, encouraging, and maintain a professional tone throughout.
"""

model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            safety_settings=safety_settings,
            )
    except Exception as e:
        st.error(f"Failed to initialize Google Generative AI: {e}")
        model = None
else:
    st.error("Gemini API key not found. Please set the GEMINI_API_KEY environment variable.")

def intelligent_ai(user_question, user_info, chat_history):
    if not model:
        return "AI functionality is disabled due to missing API key or initialization error."

    try:
        response = model.generate_content(
            chat_history + [{'role': 'user', 'parts': [user_question]}]
        )

        if not response.candidates:
            block_reason = "Unknown"
            safety_ratings_text = "N/A"
            try:
                if response.prompt_feedback:
                    block_reason = response.prompt_feedback.block_reason or "Not specified"
                    safety_ratings = response.prompt_feedback.safety_ratings
                    safety_ratings_text = ", ".join([f"{rating.category.name}: {rating.probability.name}" for rating in safety_ratings]) if safety_ratings else "None"
            except Exception:
                 pass
            st.warning(f"The AI response was blocked. Reason: {block_reason}. Safety Ratings: {safety_ratings_text}")
            return f"I cannot provide a response to that request due to content restrictions. (Reason: {block_reason})"

        if not response.text:
             st.warning("The AI generated an empty response. It might be expecting a different input or function call.")
             return "Hmm, I seem to be speechless. Could you try rephrasing?"

        return response.text

    except Exception as e:
        st.error(f"An error occurred while contacting the Gemini API: {e}")
        st.error(f"Error details: {str(e)}")
        return "Sorry, I encountered an technical error while processing your request. Please try again later."

def user_exists(email, json_file_path):
    try:
        if not os.path.exists(json_file_path): return False
        with open(json_file_path, "r") as file:
            content = file.read()
            if not content: return False
            users_data = json.loads(content)
        email_lower = email.lower()
        for user in users_data.get("users", []):
            if user.get("email", "").lower() == email_lower:
                return True
        return False
    except json.JSONDecodeError:
        st.error(f"Error reading user data file ({json_file_path}). It might be corrupted.")
        return False
    except FileNotFoundError:
        return False
    except Exception as e:
        st.error(f"Error checking user existence: {e}")
        return False

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup(json_file_path=JSON_FILE_PATH):
    st.subheader("Create a New Account")
    with st.form("signup_form"):
        name = st.text_input("Name:")
        email = st.text_input("Email:")
        age = st.number_input("Age:", min_value=1, max_value=120, step=1)
        gender = st.radio("Gender:", ("Male", "Female", "Other", "Prefer not to say"))
        skills = st.text_area("Enter your key skills (comma-separated):")
        experience = st.radio("Experience Level:", ("Fresher", "Experienced"))
        password = st.text_input("Password:", type="password")
        confirm_password = st.text_input("Confirm Password:", type="password")

        if st.form_submit_button("Signup"):
            if not name: st.error("Name field cannot be empty.")
            elif not email: st.error("Email field cannot be empty.")
            elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
                 st.error("Invalid email format.")
            elif user_exists(email, json_file_path):
                 st.error("User with this email already exists. Please login or use a different email.")
            elif not skills: st.error("Please enter your skills.")
            elif not password or len(password) < 6: st.error("Password must be at least 6 characters long.")
            elif password != confirm_password: st.error("Passwords do not match.")
            else:
                user = create_account(
                    name, email, age, gender, skills, experience, password, json_file_path
                )
                if user:
                    st.session_state["logged_in"] = True
                    st.session_state["user_info"] = user
                    st.session_state["previous_questions"] = []
                    st.success("Signup successful! You are now logged in.")
                    st.rerun()

def check_login(username, password, json_file_path=JSON_FILE_PATH):
    try:
        if not os.path.exists(json_file_path):
             st.error("User database not found. Please signup.")
             return None
        with open(json_file_path, "r") as json_file:
            content = json_file.read()
            if not content:
                st.error("User database is empty. Please signup.")
                return None
            data = json.loads(content)

        hashed_password = hash_password(password)
        username_lower = username.lower()

        for user in data.get("users", []):
            if user.get("email", "").lower() == username_lower and user.get("password") == hashed_password:
                st.session_state["logged_in"] = True
                st.session_state["user_info"] = user
                st.session_state["previous_questions"] = user.get("chat_history", [])
                st.success("Login successful!")
                return user
        return None
    except json.JSONDecodeError:
       st.error("User database file is corrupted. Cannot log in.")
       return None
    except FileNotFoundError:
       st.error("User database not found. Please signup.")
       return None
    except Exception as e:
        st.error(f"Error checking login: {e}")
        return None

def initialize_database(json_file_path=JSON_FILE_PATH):
    try:
        if not os.path.exists(json_file_path):
            data = {"users": []}
            with open(json_file_path, "w") as json_file:
                json.dump(data, json_file, indent=4)
    except Exception as e:
        st.error(f"Error initializing database: {e}")

def create_account(name, email, age, gender, skills, experience, password, json_file_path=JSON_FILE_PATH):
    try:
        data = {"users": []}
        if os.path.exists(json_file_path) and os.path.getsize(json_file_path) > 0:
            try:
                with open(json_file_path, "r") as json_file:
                    data = json.load(json_file)
                if "users" not in data or not isinstance(data["users"], list):
                    data["users"] = []
            except json.JSONDecodeError:
                 st.error("Error reading user data file. Creating a new one.")
                 data = {"users": []}
        elif not os.path.exists(json_file_path):
             pass

        hashed_password = hash_password(password)
        user_info = {
            "name": name,
            "email": email.lower(),
            "age": age,
            "gender": gender,
            "skills": skills,
            "experience": experience,
            "password": hashed_password,
            "exams": None,
            "highlights": None,
            "chat_history": []
        }

        data["users"].append(user_info)

        with open(json_file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

        return user_info

    except Exception as e:
        st.error(f"Error creating account: {e}")
        return None

def login(json_file_path=JSON_FILE_PATH):
    st.subheader("Login to Your Account")
    username = st.text_input("Email:")
    password = st.text_input("Password:", type="password")

    login_button = st.button("Login")

    if login_button:
        if not username or not password:
             st.warning("Please enter both email and password.")
        else:
            user = check_login(username, password, json_file_path)
            if user is not None:
                 st.rerun()
            else:
                 if os.path.exists(json_file_path):
                     st.error("Invalid email or password. Please try again.")

def stream_data(text):
    if isinstance(text, str):
         words = re.split(r'(\s+)', text)
         for word in words:
             if word:
                 yield word
                 time.sleep(0.015)
    else:
         yield "Assistant could not provide a text response."

def render_dashboard(user_info):
    try:
        st.title(f"Welcome, {user_info.get('name', 'User')}!")
        st.subheader("Your Profile")
        st.info(f"**Name:** {user_info.get('name', 'N/A')}")
        st.info(f"**Gender:** {user_info.get('gender', 'N/A')}")
        st.info(f"**Age:** {user_info.get('age', 'N/A')}")
        st.info(f"**Skills:** {user_info.get('skills', 'N/A')}")
        st.info(f"**Experience:** {user_info.get('experience', 'N/A')}")
    except Exception as e:
        st.error(f"Error rendering Profile: {e}")

def save_chat_history(email, history, json_file_path=JSON_FILE_PATH):
     try:
         if not os.path.exists(json_file_path):
             st.error("User data file not found. Cannot save history.")
             return

         with open(json_file_path, "r") as json_file:
            content = json_file.read()
            if not content:
                st.error("User data file is empty. Cannot save history.")
                return
            data = json.loads(content)

         user_found = False
         email_lower = email.lower()
         for i, user in enumerate(data.get("users", [])):
             if user.get("email", "").lower() == email_lower:
                 MAX_HISTORY = 50
                 limited_history = history[-(MAX_HISTORY * 2):]
                 data["users"][i]["chat_history"] = limited_history
                 user_found = True
                 break

         if user_found:
             with open(json_file_path, "w") as json_file:
                 json.dump(data, json_file, indent=4)

     except (FileNotFoundError, json.JSONDecodeError) as e:
         st.error(f"Error accessing user data file to save history: {e}")
     except Exception as e:
         st.error(f"An unexpected error occurred while saving chat history: {e}")

def main(json_file_path=JSON_FILE_PATH):
    with st.sidebar:
        st.title("TalentScout AI")
        if st.session_state.get("logged_in"):
            email_display = st.session_state.get("user_info", {}).get("email", "N/A")
            st.write(f"Logged in as: {email_display}")
            page = st.radio(
                "Navigation",
                ("Profile", "AI Hiring Assistant"),
                key="page_nav_logged_in"
            )
            if st.button("Logout"):
                if st.session_state.get("user_info") and st.session_state.get("previous_questions"):
                     save_chat_history(
                         st.session_state["user_info"]["email"],
                         st.session_state["previous_questions"],
                         json_file_path
                     )
                keys_to_clear = ["logged_in", "user_info", "previous_questions"]
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("You have been logged out successfully!")
                st.rerun()
        else:
            page = st.radio(
                "Navigation",
                ("Login / Signup",),
                key="page_nav_logged_out"
            )

    if page == "Login / Signup":
        login_or_signup = st.radio(
            "Select an option", ("Login", "Signup"), key="login_signup_radio", horizontal=True
        )
        if login_or_signup == "Login":
            login(json_file_path)
        else:
            signup(json_file_path)

    elif page == "Profile":
        if st.session_state.get("logged_in") and st.session_state.get("user_info"):
            render_dashboard(st.session_state["user_info"])
        else:
            st.warning("Please login/signup to view your profile.")

    elif page == "AI Hiring Assistant":
        if st.session_state.get("logged_in") and st.session_state.get("user_info"):
            st.title("AI Hiring Assistant")

            if model and not st.session_state.get("previous_questions"):
                st.info("Starting new screening session...")
                initial_history = [{'role': 'user', 'parts': [SYSTEM_PROMPT]}]
                with st.spinner("AI is starting the conversation..."):
                    try:
                        response = model.generate_content(initial_history)
                        if response.text:
                            st.session_state.previous_questions = initial_history + [{'role': 'model', 'parts': [response.text]}]
                            with st.chat_message("assistant", avatar="🧠"):
                                st.write(response.text)
                        else:
                            st.warning("AI could not start the conversation. Please try refreshing.")
                            st.session_state.previous_questions = []
                    except Exception as e:
                         st.error(f"Error starting AI conversation: {e}")
                         st.session_state.previous_questions = []

            for i, message in enumerate(st.session_state.get("previous_questions", [])):
                 if i == 0 and message['role'] == 'user':
                     continue

                 avatar = "👤" if message["role"] == "user" else "🧠"
                 with st.chat_message(message["role"], avatar=avatar):
                     parts_content = " ".join(part for part in message.get("parts", []) if isinstance(part, str))
                     st.write(parts_content)

            if user_input := st.chat_input("Your response..."):
                st.session_state.previous_questions.append({"role": "user", "parts": [user_input]})

                with st.chat_message("user", avatar="👤"):
                    st.write(user_input)

                if model:
                    with st.spinner("Thinking..."):
                        ai_response = intelligent_ai(
                            user_input,
                            st.session_state["user_info"],
                            st.session_state["previous_questions"]
                        )

                    if ai_response:
                        st.session_state.previous_questions.append({"role": "model", "parts": [ai_response]})

                    with st.chat_message("assistant", avatar="🧠"):
                        st.write_stream(stream_data(ai_response))
                else:
                     st.error("AI model is not available. Cannot process request.")

        else:
            st.warning("Please login/signup to access the AI Hiring Assistant.")

if __name__ == "__main__":
    initialize_database(JSON_FILE_PATH)
    if not model and not GEMINI_API_KEY:
         st.warning("AI features are disabled. Please set the GEMINI_API_KEY environment variable in your .env file.")
    elif not model and GEMINI_API_KEY:
         st.error("AI model failed to initialize even though API key was found. Check console errors.")
    main(JSON_FILE_PATH)
### TalentScout-An-AI-Hiring-Assistant
# Overview
1.This is Streamlit application, developed using Python,Google Generative AI, Gemini pro model.
2.The target audience of this this application are the people who are seeking a job oppurtunities and learning new skills based on the roles.
3. It has the capability to guide you to get a job,based on the mentined skills and given details.
4.The accuracy of data increses based on the given question, so, the precise question will get accurate response.

# Installation
1. Streamlit, Google.GenerativeAI, re, hashlib,dotenv,etc. By mentioning all installation, created "requirements.txt", we can easily install required libraries.
2. we can download and istall using pip
   "!pip install -r requirements.txt"
3. We need to virtual environment to install all libraries and for managing all the thigs in the project
   >python -m venv venv
4.After creating venv, Need to activate environment
   >venv\Scripts\activate
   the environment installment is different from Anaconda, If youre using conda, Different exist for creating venv and for activating.
5. After successful coding, We can run Application using this command
   >streamlit run your_app.py
# Gemini Api and Promt creation
1.Gemini model like "gemini-1.5-flash" is used.
2.The prompt is created in organised way to engage user by wishing,asking required details,giving suggestions,checking knowledge in mentioned skills of a user.
3. The prompt and user queries and passed and maintaining continuity by saving previous queries to save from deviations.

# challenges & solutions
1. The API keys are not totally free,so, I faced problem when im using OpenAI API key, it doesnt allow to ask question, its like showing your tokens are over.
2. For that I changed OpenAI API key to GEMINI API keys because it allowed to pass questions.
3. Bugs are quite common while creating project, Resolved IT.
4. The application works better, if we use paid API key for better result.
5. Its open sourced and allows for only limited queries.

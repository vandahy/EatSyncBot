import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('models/gemini-2.5-flash-preview-09-2025') # Use exact name from list

try:
    print("Testing raw gemini-2.5-flash-preview-09-2025...")
    response = model.generate_content("Hello")
    print(f"Success: {response.text}")
except Exception as e:
    print(f"Error: {e}")

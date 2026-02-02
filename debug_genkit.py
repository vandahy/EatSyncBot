import asyncio
import os
from genkit.ai import Genkit
from genkit.plugins.google_genai import GoogleAI
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
os.environ["GOOGLE_GENAI_API_KEY"] = API_KEY

print(f"--- TESTING GENKIT WITH API KEY: {API_KEY[:5]}... ---")

# Danh sách các model tiềm năng cần test
models_to_test = [
    'googleai/gemini-1.5-flash',
    'googleai/gemini-2.0-flash', 
    'googleai/gemini-2.5-flash',
    'googleai/gemini-2.5-flash-preview-09-2025',
    'googleai/gemini-1.5-pro'
]

async def test_model(model_name):
    print(f"\n👉 Testing model: {model_name}")
    try:
        ai = Genkit(plugins=[GoogleAI()], model=model_name)
        response = await ai.generate(prompt="Hello, are you working?")
        print(f"✅ SUCCESS! Response: {response.text}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

async def main():
    success_count = 0
    for m in models_to_test:
        if await test_model(m):
            success_count += 1
            print(f"*** FOUND WORKING MODEL: {m} ***")
            break # Tìm thấy cái chạy được là dừng luôn
    
    if success_count == 0:
        print("\n⚠️ ALL MODELS FAILED in Genkit.")
    else:
        print("\n🎉 DONE.")

if __name__ == "__main__":
    asyncio.run(main())

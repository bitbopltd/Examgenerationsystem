
import google.generativeai as genai
import os

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

try:
    genai.configure(api_key=api_key)
    print("Attempting to list models...")
    
    for m in genai.list_models():
        print(f"- Name: {m.name}")
        print(f"  Display Name: {m.display_name}")
        print(f"  Supported Methods: {m.supported_generation_methods}")
        
        if 'generateContent' in m.supported_generation_methods and ('gemini-pro' in m.name or 'gemini-1.0-pro' in m.name):
            print(f"  *** Found Gemini Pro model: {m.name}")
            
except Exception as e:
    print(f"Error during API check: {e}")

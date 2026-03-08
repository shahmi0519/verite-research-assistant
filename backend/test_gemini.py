import google.generativeai as genai
import os

# Configure your API key
genai.configure(api_key="AIzaSyAdXIJ6iD2FW6-kt02eTVr-3ccdPRaTFt8")

# Iterate through available models
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Model Name: {m.name}")
        print(f"Display Name: {m.display_name}")
        print("-" * 20)

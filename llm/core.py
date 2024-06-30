import sys
import os
from config.keys import API_KEYS

import google.generativeai as genai

genai.configure(api_key=API_KEYS.GEMINI)

model = genai.GenerativeModel('gemini-1.5-flash')

response = model.generate_content("Write a story about a AI and magic")

print(response.text)
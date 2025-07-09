# config.py
import streamlit as st
import os

# Try to get API key from Streamlit secrets first, then environment variable, then default
try:
 GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
 GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")

# For development, you can still put your key directly here:
# GEMINI_API_KEY = "your_actual_api_key_here"

import subprocess
import sys
import os

def install_requirements():
    requirements = [
        "streamlit",
        "playwright",
        "playwright-stealth", 
        "beautifulsoup4",
        "newspaper3k",
        "pandas",
        "openpyxl",
        "google-generativeai",
        "requests",
        "lxml"
    ]

    print("Installing Python packages...")
    for requirement in requirements:
        print(f"Installing {requirement}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", requirement])

    print("Installing playwright browsers...")
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

    print("\n" + "="*50)
    print("SETUP SELESAI!")
    print("="*50)
    print("\nLangkah selanjutnya:")
    print("1. Buka file config.py")
    print("2. Ganti YOUR_GEMINI_API_KEY_HERE dengan API key Gemini Anda")
    print("3. Jalankan aplikasi dengan: streamlit run app.py")
    print("\nUntuk mendapatkan API key Gemini:")
    print("- Kunjungi: https://makersuite.google.com/app/apikey")
    print("- Buat API key baru")
    print("- Copy dan paste ke config.py")

if __name__ == "__main__":
    install_requirements()

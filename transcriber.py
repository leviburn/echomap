# transcriber.py

import openai
import os
from dotenv import load_dotenv

# Force load .env from the current working directory
load_dotenv(dotenv_path=os.path.join(os.getcwd(), '.env'))

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcribe_audio(filepath):
    print(f"[+] Transcribing file: {filepath}")
    with open(filepath, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

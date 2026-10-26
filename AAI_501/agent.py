import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
GEMINI_API_KEY = os.environ['AAI_SECRET']
client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_ID = "gemini-3.8-flash" # @param ["gemini-4-argon", "gemini-3.1-pro-preview", "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-2.5-pro"] {"allow-input": true, "isTemplate": true}

print("Sending request to Gemini (60-second request timeout)...", flush=True)
interaction = client.interactions.create(
    model=MODEL_ID,
    input="Please give me python code to sort a list.",
    timeout=60.0,
)

print("Response received.", flush=True)
print(interaction.steps[-1].content[0].text)

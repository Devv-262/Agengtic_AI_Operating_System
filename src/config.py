import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# We will use Groq for the free, ultra-fast LLM API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY is not set in the .env file.")

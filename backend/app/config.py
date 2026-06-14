import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve .env file relative to project root
env_path = Path(__file__).parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

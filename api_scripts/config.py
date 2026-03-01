import os
from dotenv import load_dotenv

load_dotenv()

API_HOST = "aerodatabox.p.rapidapi.com"
API_KEY = os.getenv("RAPIDAPI_KEY")

if not API_KEY:
    raise ValueError("RAPIDAPI_KEY not found in environment variables")

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST
}

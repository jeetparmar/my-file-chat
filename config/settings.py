from datetime import datetime
import os

# Application Info
APP_NAME = "My File Chat"
APP_HEADER = "💬 My File Chat"
APP_HEADER_CAPTION = (
    "🚀 This chatbot is created using the open-source Llama 2 LLM model from Meta."
)
CURRENT_YEAR = datetime.now().year
COMPANY_NAME = "JSP Group"

# URLs and Icons
ICON_URL = (
    "https://raw.githubusercontent.com/jeetparmar/my-file-chat/refs/heads/main/logo.png"
)
FULL_ICON_URL = "https://raw.githubusercontent.com/jeetparmar/my-file-chat/refs/heads/main/file-chat.png"

# File Types
VALID_AUDIO_TYPES = ".wav", ".mp3", ".m4a"
VALID_IMAGE_TYPES = ".png", ".jpg", ".jpeg"
VALID_ALL_TYPES = ["pdf", "txt", "mp3", "m4a", "wav", "mp4", "png", "jpeg", "jpg"]

# UI Tabs
FILE_TABS = ["**Preview**", "**Transcript**", "**Keywords**", "**Summary**"]

# Database
MONGODB_CONNECTION_STRING = os.getenv(
    "MONGODB_CONNECTION_STRING", "mongodb://localhost:27017/mychatdb"
)
DB_NAME = "chat-app"
COLLECTIONS = {"chat_data": "chat-data", "group_data": "group-data"}

# OTP (for demo purposes)
DEMO_OTP = "123456"

# Text Processing
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_KEYWORDS = 100
MIN_KEYWORDS = 5
DEFAULT_KEYWORDS = 10

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# AI Models
SUMMARY_MODEL = "chatgpt-4o-latest"
MAX_MODEL_TOKENS = 50000
SUMMARIZER_TEMPERATURE = 0

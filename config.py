import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")

# Application Settings
APP_TITLE = "High-Performance Prospecting App"
APP_ICON = "🚀"

# Scraping Settings
SEARCH_RADIUS_METERS = 5000  # Default search radius
MAX_RESULTS_PER_SEARCH = 60  # Google Maps API default limit per token

# Database Settings
DB_PATH = "prospects.db"

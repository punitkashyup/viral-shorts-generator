"""Configuration settings for the Viral Shorts Generator."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
TEMP_DIR = BASE_DIR / os.getenv("TEMP_DIR", "temp")
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "output")

# Create directories if they don't exist
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# OpenAI Settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Whisper Settings
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

# Video Settings
MAX_CLIP_DURATION = int(os.getenv("MAX_CLIP_DURATION", 60))
VIDEO_FORMAT = os.getenv("VIDEO_FORMAT", "mp4")
OUTPUT_RESOLUTION = (1080, 1920)  # 9:16 aspect ratio for shorts
OUTPUT_FPS = 30

# Text Animation Settings
DEFAULT_FONT = "Arial-Bold"
DEFAULT_FONT_SIZE = 70
DEFAULT_TEXT_COLOR = "white"
DEFAULT_STROKE_COLOR = "black"
DEFAULT_STROKE_WIDTH = 3

# Animation types
ANIMATION_TYPES = ["fade_in", "slide_up", "pop", "typewriter", "shake", "glow"]

def validate_config():
    """Validate that required configuration is present."""
    errors = []
    
    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is not set. Please add it to your .env file.")
    
    if errors:
        raise ValueError("\n".join(errors))
    
    return True

"""
LLM Client - Gemini API wrapper for CramClutch
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found in environment variables. "
        "Please set it in your .env file or environment."
    )

# Configure Gemini API
genai.configure(api_key=api_key)

# Initialize model
model = genai.GenerativeModel("gemini-2.5-flash-lite")


def generate_response(prompt: str) -> str:
    """
    Generate response from Gemini LLM
    
    Args:
        prompt: Input prompt text
    
    Returns:
        str: Generated response text
    """
    response = model.generate_content(prompt)
    return response.text

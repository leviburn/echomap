import openai
import os
import logging
from dotenv import load_dotenv

# Configure logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_client():
    """Create and return an OpenAI client with error handling"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.critical("OPENAI_API_KEY not set in environment variables")
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    return openai.OpenAI(api_key=api_key)

def transcribe_audio(filepath):
    """
    Transcribe an audio file using OpenAI's Whisper API
    
    Args:
        filepath (str): Path to the audio file
        
    Returns:
        str: The transcribed text
        
    Raises:
        FileNotFoundError: If the audio file doesn't exist
        ValueError: If the API key is not set or invalid
        Exception: For other API errors
    """
    logger.info(f"Transcribing file: {filepath}")
    
    # Check if file exists
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        raise FileNotFoundError(f"Audio file not found: {filepath}")
    
    # Check file size (Whisper API limit is 25MB)
    file_size = os.path.getsize(filepath) / (1024 * 1024)  # Convert to MB
    if file_size > 25:
        logger.error(f"File too large: {file_size:.2f}MB (max 25MB)")
        raise ValueError(f"Audio file too large: {file_size:.2f}MB (max 25MB)")
    
    try:
        client = get_client()
        
        with open(filepath, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        logger.info("Transcription successful")
        return response.text
        
    except openai.APIError as e:
        logger.error(f"API error: {str(e)}")
        raise Exception(f"OpenAI API error: {str(e)}")
    except openai.APIConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        raise Exception(f"Connection error: {str(e)}")
    except openai.RateLimitError as e:
        logger.error(f"Rate limit error: {str(e)}")
        raise Exception("API rate limit exceeded. Please try again later.")
    except Exception as e:
        logger.error(f"Unexpected error during transcription: {str(e)}")
        raise
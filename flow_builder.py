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

def generate_flowchart(transcript):
    """
    Generate a mermaid flowchart based on a transcript
    
    Args:
        transcript (str): The transcript text
        
    Returns:
        str: The mermaid flowchart code
        
    Raises:
        ValueError: If the API key is not set or invalid
        Exception: For other API errors
    """
    if not transcript or not transcript.strip():
        logger.error("Empty transcript provided")
        raise ValueError("Cannot generate flowchart from empty transcript")
    
    logger.info("Generating flowchart from transcript")
    
    try:
        client = get_client()
        
        # Create a well-structured prompt
        prompt = f"""
        Create a mermaid flowchart based on the following IVR (Interactive Voice Response) transcript:
        
        {transcript}
        
        Guidelines:
        - Start with a clear flowchart diagram type (flowchart TD for top-down)
        - Use descriptive node IDs
        - Represent menu options clearly
        - Include all possible user paths
        - Keep the flowchart clean and readable
        - Use appropriate formatting for nodes (rectangles for processes, diamonds for decisions)
        
        Return ONLY the mermaid flowchart code with no explanations or additional text.
        """
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a specialized assistant that creates accurate mermaid flowcharts from IVR transcripts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,  # Balance between creativity and determinism
            max_tokens=2000   # Allow sufficient length for complex flowcharts
        )
        
        flowchart = response.choices[0].message.content.strip()
        logger.info("Flowchart generated successfully")
        
        return flowchart
        
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
        logger.error(f"Unexpected error during flowchart generation: {str(e)}")
        raise
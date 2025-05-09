from flask import Flask, render_template, request, flash, redirect, url_for
import os
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from transcriber import transcribe_audio
from flow_builder import generate_flowchart
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure application
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit uploads to 16MB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav', 'ogg', 'm4a'}
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def index():
    transcript = None
    flowchart = None
    error = None

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    if request.method == 'POST':
        logger.debug("Received POST request")
        
        # Check if file part exists in request
        if 'file' not in request.files:
            logger.debug("No file part in the request")
            return render_template('index.html', error="No file uploaded.")

        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            logger.debug("No selected file")
            return render_template('index.html', error="No file selected.")

        # Validate file type
        if not allowed_file(file.filename):
            logger.debug(f"Invalid file type: {file.filename}")
            return render_template('index.html', error="Invalid file type. Please upload MP3, WAV, OGG, or M4A files.")

        try:
            # Save file securely
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            logger.debug(f"Saved file to: {filepath}")

            # Transcribe audio
            try:
                transcript = transcribe_audio(filepath)
                logger.debug(f"Generated transcript: {transcript}")
                
                # Generate flowchart
                try:
                    flowchart = generate_flowchart(transcript)
                    logger.debug("Flowchart generated successfully")
                    
                    # Remove triple backticks and 'mermaid' tag if present
                    if flowchart.startswith("```") and "```" in flowchart:
                        flowchart = "\n".join(flowchart.split("\n")[1:])
                        if flowchart.endswith("```"):
                            flowchart = flowchart[:-3]
                    
                    logger.debug(f"Processed flowchart: {flowchart}")
                except Exception as e:
                    logger.error(f"Error generating flowchart: {str(e)}")
                    error = f"Error generating flowchart: {str(e)}"
            except Exception as e:
                logger.error(f"Error transcribing audio: {str(e)}")
                error = f"Error transcribing audio: {str(e)}"
        
        except RequestEntityTooLarge:
            logger.error("File too large")
            error = "File too large. Maximum size is 16MB."
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            error = f"An unexpected error occurred: {str(e)}"

    return render_template('index.html', transcript=transcript, flowchart=flowchart, error=error)

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    logger.error("File too large (413)")
    return render_template('index.html', error="File too large. Maximum size is 16MB."), 413

@app.errorhandler(500)
def internal_server_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {str(error)}")
    return render_template('index.html', error="Internal server error. Please try again later."), 500

if __name__ == '__main__':
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        logger.critical("OPENAI_API_KEY not set in environment variables")
        print("ERROR: OPENAI_API_KEY not set. Please set it in your .env file.")
        exit(1)
    
    app.run(debug=True)
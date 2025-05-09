# EchoMap: IVR Flowchart Generator

EchoMap is a web application that transcribes IVR (Interactive Voice Response) audio recordings and automatically generates visual flowcharts from them.

## Features

- Audio transcription using OpenAI's Whisper model
- Automatic flowchart generation from transcripts using GPT-4
- Interactive visualization with Mermaid.js
- Clean, responsive web interface
- Support for multiple audio formats

## Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. Clone the repository or download the source code

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create an environment file:
   ```bash
   cp .env.example .env
   ```

5. Edit the `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

### Running the Application

Start the Flask development server:
```bash
python app.py
```

The application will be available at `http://127.0.0.1:5000/`

## Project Structure

- `app.py` - Main Flask application
- `transcriber.py` - Audio transcription module using OpenAI's Whisper
- `flow_builder.py` - Flowchart generation using GPT-4
- `templates/index.html` - Web interface template
- `uploads/` - Directory for uploaded audio files (created automatically)

## Usage

1. Open the application in your web browser
2. Upload an IVR audio recording (supported formats: MP3, WAV, OGG, M4A)
3. Wait for the transcription and flowchart generation process
4. View the transcript and interactive flowchart

## Technical Details

- **Transcription**: Uses OpenAI's Whisper model for accurate speech-to-text conversion
- **Flowchart Generation**: Leverages GPT-4 to interpret the transcript and create a structured flowchart
- **Visualization**: Rendered with Mermaid.js for interactive diagrams
- **Web Framework**: Built with Flask

## Limitations

- Audio files are limited to 16MB (Flask configuration) and 25MB (Whisper API limit)
- Complex IVR systems may require manual adjustment of the generated flowcharts
- The application requires an internet connection to use OpenAI's APIs


## License

[MIT License](LICENSE)
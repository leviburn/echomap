from flask import Flask, render_template, request
import os
from werkzeug.utils import secure_filename
from transcriber import transcribe_audio
from dotenv import load_dotenv
import openai
import logging

load_dotenv()
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/', methods=['GET', 'POST'])
def index():
    transcript = None
    flowchart = None

    if request.method == 'POST':
        logging.debug("Received POST request")
        if 'file' not in request.files:
            logging.debug("No file part in the request")
            return render_template('index.html', transcript="No file uploaded.")

        file = request.files['file']
        if file.filename == '':
            logging.debug("No selected file")
            return render_template('index.html', transcript="No file selected.")

        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        logging.debug(f"Saved file to: {filepath}")

        transcript = transcribe_audio(filepath)
        logging.debug(f"Generated transcript: {transcript}")

        prompt = f"""
        Create a mermaid flowchart based on the following transcript:
        {transcript}

        Return only the mermaid flowchart code.
        """

        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates mermaid flowcharts."},
                {"role": "user", "content": prompt}
            ]
        )

        flowchart = completion.choices[0].message.content.strip()

        # Remove triple backticks and 'mermaid' tag if present
        if flowchart.startswith("```") and flowchart.endswith("```"):
            flowchart = "\n".join(flowchart.strip("`").split("\n")[1:])

        logging.debug(f"Generated flowchart: {flowchart}")

    return render_template('index.html', transcript=transcript, flowchart=flowchart)

if __name__ == '__main__':
    app.run()

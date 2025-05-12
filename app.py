from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify, Response
import os
import tempfile
import json
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from transcriber import transcribe_audio
from flow_builder import generate_flowchart
from analytics import IVRAnalytics
from dotenv import load_dotenv
import logging
import time
from voxo_integration import initiate_call_and_record, get_call_recording, get_transcript_from_voxo
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client

# Load environment variables
load_dotenv()

# Configure application
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit uploads to 16MB
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav', 'ogg', 'm4a'}
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))

# For Render free tier (no persistent disk), use temp directory
if os.getenv('RENDER', 'False').lower() == 'true':
    app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
    app.config['USE_TEMP_FILES'] = True
else:
    # Local development uses local uploads directory
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['USE_TEMP_FILES'] = False

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv('FLASK_DEBUG', 'False').lower() == 'true' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory store for latest analysis (for demo purposes)
latest_analysis = {
    'transcript': '',
    'flowchart': '',
    'metrics': {},
    'summary': '',
    'visualization_data': {},
    'dtmf_sequence': [],
    'timestamp': None
}

def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def index():
    logger.info(f"[ROUTE] / (index) {request.method} {request.path}")
    start_time = time.time()
    transcript = None
    flowchart = None
    error = None

    # Ensure upload directory exists (for local development)
    if not app.config['USE_TEMP_FILES']:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        logger.debug(f"Ensured upload directory exists: {app.config['UPLOAD_FOLDER']}")

    if request.method == 'POST':
        upload_time = time.time()
        logger.info("Received POST request for file upload")
        is_ajax = request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html
        
        # Check if file part exists in request
        if 'file' not in request.files:
            logger.warning("No file part in the request")
            print(f"[PROFILE] File upload: {time.time() - upload_time:.2f}s")
            if is_ajax:
                return jsonify({'error': "No file uploaded."}), 400
            return render_template('index.html', error="No file uploaded."), 400

        file = request.files['file']
        logger.debug(f"File received: {file.filename}")
        
        # Check if file was selected
        if file.filename == '':
            logger.warning("No selected file")
            print(f"[PROFILE] File upload: {time.time() - upload_time:.2f}s")
            if is_ajax:
                return jsonify({'error': "No file selected."}), 400
            return render_template('index.html', error="No file selected."), 400

        # Validate file type
        if not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            print(f"[PROFILE] File upload: {time.time() - upload_time:.2f}s")
            if is_ajax:
                return jsonify({'error': "Invalid file type. Please upload MP3, WAV, OGG, or M4A files."}), 400
            return render_template('index.html', error="Invalid file type. Please upload MP3, WAV, OGG, or M4A files."), 400
        logger.info(f"File validated: {file.filename}")
        print(f"[PROFILE] File upload: {time.time() - upload_time:.2f}s")

        try:
            # Save file securely (using different methods based on environment)
            if app.config['USE_TEMP_FILES']:
                suffix = '.' + file.filename.rsplit('.', 1)[1].lower()
                temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
                file.save(temp_file.name)
                filepath = temp_file.name
                logger.info(f"Saved file to temporary location: {filepath}")
            else:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                logger.info(f"Saved file to: {filepath}")

            # Transcribe audio
            transcription_time = time.time()
            logger.info(f"Starting transcription for file: {filepath}")
            try:
                transcript = transcribe_audio(filepath)
                logger.info(f"Transcription complete. Transcript length: {len(transcript)} characters")
                logger.debug(f"Transcript preview: {transcript[:100]}")
                
                # Generate flowchart
                flowchart_time = time.time()
                logger.info("Starting flowchart generation")
                try:
                    flowchart = generate_flowchart(transcript)
                    logger.info(f"Flowchart generated. Length: {len(flowchart)} characters")
                    
                    # Remove triple backticks and 'mermaid' tag if present
                    if flowchart.startswith("```") and "```" in flowchart:
                        flowchart = "\n".join(flowchart.split("\n")[1:])
                        if flowchart.endswith("```"):
                            flowchart = flowchart[:-3]
                    logger.debug(f"Processed flowchart preview: {flowchart[:100]}")
                except Exception as e:
                    logger.error(f"Error generating flowchart: {str(e)}", exc_info=True)
                    if is_ajax:
                        return jsonify({'error': f"Error generating flowchart: {str(e)}"}), 500
                    return render_template('index.html', error=f"Error generating flowchart: {str(e)}"), 500
            except Exception as e:
                logger.error(f"Error transcribing audio: {str(e)}", exc_info=True)
                if is_ajax:
                    return jsonify({'error': f"Error transcribing audio: {str(e)}"}), 500
                return render_template('index.html', error=f"Error transcribing audio: {str(e)}"), 500
            
            # Clean up temporary file if using temp files
            if app.config['USE_TEMP_FILES'] and os.path.exists(filepath):
                try:
                    os.unlink(filepath)
                    logger.info(f"Deleted temporary file: {filepath}")
                except Exception as e:
                    logger.warning(f"Could not delete temporary file: {str(e)}", exc_info=True)
            
            # Analytics
            analytics_time = time.time()
            logger.info("Starting analytics generation")
            try:
                analytics = IVRAnalytics(transcript, flowchart)
                metrics = analytics.get_metrics()
                summary = analytics.get_summary()
                visualization_data = analytics.get_visualization_data()
                logger.info("Analytics complete")
                logger.debug(f"Metrics keys: {list(metrics.keys())}")
                logger.debug(f"Summary: {summary}")
                print(f"[PROFILE] Flowchart: {time.time() - flowchart_time:.2f}s")
                print(f"[PROFILE] Analytics: {time.time() - analytics_time:.2f}s")
                print(f"[PROFILE] Total processing time: {time.time() - start_time:.2f}s")
                logger.info("Rendering insights page")
                if is_ajax:
                    return jsonify({'transcript': transcript, 'flowchart': flowchart}), 200
                return render_template(
                    'insights.html',
                    transcript=transcript,
                    flowchart=flowchart,
                    metrics=metrics,
                    summary=summary,
                    visualization_data=json.dumps(visualization_data)
                )
            except Exception as e:
                logger.error(f"Error generating insights: {str(e)}", exc_info=True)
                if is_ajax:
                    return jsonify({'error': f"Error generating insights: {str(e)}"}), 500
                flash(f"Error generating insights: {str(e)}", 'error')
                return render_template('index.html', error=f"Error generating insights: {str(e)}"), 500
        
        except RequestEntityTooLarge:
            logger.error("File too large (413)", exc_info=True)
            if is_ajax:
                return jsonify({'error': "File too large. Maximum size is 16MB."}), 413
            return render_template('index.html', error="File too large. Maximum size is 16MB."), 413
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            if is_ajax:
                return jsonify({'error': f"An unexpected error occurred: {str(e)}"}), 500
            return render_template('index.html', error=f"An unexpected error occurred: {str(e)}"), 500

    logger.info("Rendering index page")
    return render_template('index.html', transcript=transcript, flowchart=flowchart, error=error)

@app.route('/insights', methods=['GET', 'POST'])
def insights():
    logger.info(f"[ROUTE] /insights {request.method} {request.path}")
    transcript = request.args.get('transcript', '')
    flowchart = request.args.get('flowchart', '')
    
    if not transcript or not flowchart:
        logger.warning('No IVR data available for analysis. Redirecting to home.')
        # Try to get from session if not in query params
        transcript = session.get('transcript', '')
        flowchart = session.get('flowchart', '')
    
    # If still no transcript or flowchart, redirect to home
    if not transcript or not flowchart:
        flash('No IVR data available for analysis. Please upload an audio file first.', 'warning')
        logger.warning('No transcript or flowchart found. Redirecting to index.')
        return redirect(url_for('index'))
    
    # Store in session
    session['transcript'] = transcript
    session['flowchart'] = flowchart
    logger.debug('Transcript and flowchart stored in session.')
    
    # Generate insights
    try:
        logger.info('Generating insights for /insights route')
        analytics = IVRAnalytics(transcript, flowchart)
        metrics = analytics.get_metrics()
        summary = analytics.get_summary()
        visualization_data = analytics.get_visualization_data()
        logger.info('Insights generation complete. Rendering insights page.')
        return render_template(
            'insights.html',
            transcript=transcript,
            flowchart=flowchart,
            metrics=metrics,
            summary=summary,
            visualization_data=json.dumps(visualization_data)
        )
        
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}", exc_info=True)
        flash(f"Error generating insights: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.errorhandler(413)
def request_entity_too_large(error):
    logger.error("File too large (413)", exc_info=True)
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({'error': "File too large. Maximum size is 16MB."}), 413
    return render_template('index.html', error="File too large. Maximum size is 16MB."), 413

@app.errorhandler(500)
def internal_server_error(error):
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({'error': "Internal server error. Please try again later."}), 500
    return render_template('index.html', error="Internal server error. Please try again later."), 500

@app.route('/call-ivr', methods=['POST'])
def call_ivr():
    phone_number = request.form.get('phone_number')
    if not phone_number:
        return jsonify({'error': 'Phone number required'}), 400
    try:
        call_id = initiate_call_and_record(phone_number)
        recording_url = get_call_recording(call_id)
        transcript = get_transcript_from_voxo(call_id)
        return jsonify({'transcript': transcript, 'recording_url': recording_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/voxo-webhook', methods=['POST'])
def voxo_webhook():
    data = request.json
    event_type = data.get('eventType')
    logger.info(f"Received VOXO webhook event: {event_type}")
    if event_type == 'STARTCALL':
        logger.info(f"Call started: {data}")
    elif event_type == 'RECORDING_AVAILABLE':
        recording_url = data.get('recordingUrl')
        logger.info(f"Recording available: {recording_url}")
        # You can download/process the recording here
    elif event_type == 'TRANSCRIPTION_AVAILABLE':
        transcript = data.get('transcription')
        logger.info(f"Transcription available: {transcript[:100]}...")
        # You can trigger your IVR analysis pipeline here
    else:
        logger.warning(f"Unhandled VOXO event type: {event_type}")
    return '', 200

@app.route('/call-status', methods=['GET', 'POST'])
def call_status():
    """Handle Twilio call status updates"""
    call_sid = request.values.get('CallSid', '')
    call_status = request.values.get('CallStatus', '')
    
    logger.info(f"Call {call_sid} status updated to: {call_status}")
    
    # Store call status in session
    if call_sid and call_status:
        session[f'call_status_{call_sid}'] = call_status
        logger.info(f"Stored call status for {call_sid}: {call_status}")
    
    if call_status == 'completed':
        # Clean up any temporary data if needed
        if f'recording_{call_sid}' in session:
            del session[f'recording_{call_sid}']
    
    # For GET requests, return the current status
    if request.method == 'GET':
        # Get the latest DTMF and transcript from the session
        dtmf_sequence = session.get('dtmf_sequence', [])
        transcript = session.get('transcript', '')
        analysis = session.get(f'analysis_{call_sid}', {})
        current_status = session.get(f'call_status_{call_sid}', 'initiated')  # Default to initiated if not set
        
        # Get the current transcription status
        transcription_status = 'pending'
        if transcript:
            transcription_status = 'complete'
        elif current_status in ['in-progress', 'answered']:
            transcription_status = 'in-progress'
        
        logger.info(f"Returning status for {call_sid}: {current_status}")
        return jsonify({
            'status': current_status,
            'dtmf': dtmf_sequence[-1] if dtmf_sequence else None,
            'transcript': transcript,
            'analysis': analysis,
            'transcription_status': transcription_status
        })
    
    return ('', 200)

@app.route('/latest-analysis', methods=['GET'])
def latest_analysis_view():
    """Return the latest analysis results as JSON"""
    if not latest_analysis or not latest_analysis.get('transcript'):
        return jsonify({
            'transcript': '',
            'flowchart': '',
            'metrics': {},
            'summary': '',
            'visualization_data': {},
            'dtmf_sequence': [],
            'status': 'pending'
        })
        
    return jsonify({
        'transcript': latest_analysis['transcript'],
        'flowchart': latest_analysis['flowchart'],
        'metrics': latest_analysis['metrics'],
        'summary': latest_analysis['summary'],
        'visualization_data': latest_analysis['visualization_data'],
        'dtmf_sequence': latest_analysis.get('dtmf_sequence', []),
        'status': 'completed'
    })

@app.route('/make-call', methods=['POST'])
def make_call():
    """Initiate a new call to the specified number"""
    to_number = request.form.get('to_number')
    if not to_number:
        return jsonify({'error': 'Phone number required'}), 400

    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_number = os.getenv('TWILIO_NUMBER')
        
        if not all([account_sid, auth_token, from_number]):
            raise ValueError("Missing Twilio credentials in environment variables")
        
        client = Client(account_sid, auth_token)
        webhook_url = os.getenv('WEBHOOK_URL', request.url_root.rstrip('/'))
        logger.info(f"Using webhook URL: {webhook_url}")
        
        # Create the call with machine detection
        call = client.calls.create(
            to=to_number,
            from_=from_number,
            url=f"{webhook_url}/twilio-ivr",
            status_callback=f"{webhook_url}/call-status",
            status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
            status_callback_method='POST',
            machine_detection='DetectMessageEnd',  # Detect when answering machine message ends
            machine_detection_timeout=30,  # Wait up to 30 seconds for machine detection
            machine_detection_speech_threshold=3000,  # 3 seconds of speech to consider it a human
            machine_detection_speech_end_threshold=1000,  # 1 second of silence to consider speech ended
            machine_detection_silence_timeout=5000  # 5 seconds of silence to consider it a machine
        )
        
        # Store initial call status
        session[f'call_status_{call.sid}'] = 'initiated'
        logger.info(f"Call initiated with SID: {call.sid}, status: {call.status}")
        
        return jsonify({
            'message': 'Call initiated successfully',
            'call_sid': call.sid,
            'status': call.status
        })
        
    except Exception as e:
        logger.error(f"Error initiating call: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/twilio-ivr', methods=['POST'])
def twilio_ivr():
    """Handle incoming Twilio calls with IVR flow"""
    try:
        response = VoiceResponse()
        call_sid = request.values.get('CallSid', '')
        answered_by = request.values.get('AnsweredBy', '')
        logger.info(f"New call initiated with SID: {call_sid}, Answered by: {answered_by}")
        
        # Store initial call status
        session[f'call_status_{call_sid}'] = 'in-progress'
        
        # Check if it's a machine
        if answered_by == 'machine_start':
            logger.info("Machine detected, starting recording")
            # Start recording immediately for machine
            response.record(
                action='/recording-callback',
                method='POST',
                maxLength='300',  # 5 minutes max
                playBeep=False,  # Don't play beep since we're recording IVR
                transcribe=True,
                transcribeCallback='/transcription-callback',
                trim='trim-silence',  # Trim silence from the recording
                detect_speech=True,  # Enable speech detection
                detect_silence=True,  # Enable silence detection
                detect_silence_timeout=2  # Timeout in seconds for silence detection
            )
        else:
            # For human answers, play a brief message
            response.say("Thank you for calling. This is an automated system. Please press any key to continue.",
                       voice='alice',
                       language='en-US')
            
            # Gather DTMF input
            gather = response.gather(
                input='dtmf',
                timeout=5,  # Wait up to 5 seconds for input
                action='/handle-dtmf',
                method='POST'
            )
            
            # If no input is received, start recording anyway
            response.record(
                action='/recording-callback',
                method='POST',
                maxLength='300',
                playBeep=False,
                transcribe=True,
                transcribeCallback='/transcription-callback',
                trim='trim-silence',
                detect_speech=True,
                detect_silence=True,
                detect_silence_timeout=2
            )
        
        logger.info(f"Generated TwiML response for call {call_sid}")
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error in twilio_ivr: {str(e)}", exc_info=True)
        error_response = VoiceResponse()
        error_response.say("We're sorry, but an error occurred. Please try your call again later.",
                         voice='alice',
                         language='en-US')
        error_response.hangup()
        return Response(str(error_response), mimetype='text/xml')

@app.route('/handle-dtmf', methods=['POST'])
def handle_dtmf():
    """Handle DTMF input from the IVR"""
    try:
        response = VoiceResponse()
        digits = request.values.get('Digits', '')
        call_sid = request.values.get('CallSid', '')
        
        logger.info(f"DTMF received for call {call_sid}: {digits}")
        
        # Store the DTMF input in the session
        if 'dtmf_sequence' not in session:
            session['dtmf_sequence'] = []
        session['dtmf_sequence'].append(digits)
        
        # Start recording after DTMF input
        response.record(
            action='/recording-callback',
            method='POST',
            maxLength='300',
            playBeep=False,
            transcribe=True,
            transcribeCallback='/transcription-callback',
            trim='trim-silence',
            detect_speech=True,
            detect_silence=True,
            detect_silence_timeout=2
        )
        
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error in handle_dtmf: {str(e)}", exc_info=True)
        error_response = VoiceResponse()
        error_response.hangup()
        return Response(str(error_response), mimetype='text/xml')

@app.route('/recording-callback', methods=['POST'])
def recording_callback():
    """Handle the completed recording"""
    try:
        response = VoiceResponse()
        recording_url = request.values.get('RecordingUrl', '')
        recording_sid = request.values.get('RecordingSid', '')
        call_sid = request.values.get('CallSid', '')
        
        logger.info(f"Recording completed - SID: {recording_sid}, URL: {recording_url}")
        
        # Store recording information in session
        session[f'recording_{call_sid}'] = {
            'url': recording_url,
            'sid': recording_sid,
            'timestamp': time.time(),
            'dtmf_sequence': session.get('dtmf_sequence', [])
        }
        
        # End the call after recording is complete
        response.say("Thank you for your call. The recording is complete.",
                    voice='alice',
                    language='en-US')
        response.hangup()
        
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error in recording_callback: {str(e)}", exc_info=True)
        error_response = VoiceResponse()
        error_response.hangup()
        return Response(str(error_response), mimetype='text/xml')

@app.route('/transcription-callback', methods=['POST'])
def transcription_callback():
    """Handle the completed transcription"""
    try:
        transcription_text = request.values.get('TranscriptionText', '')
        call_sid = request.values.get('CallSid', '')
        recording_sid = request.values.get('RecordingSid', '')
        
        logger.info(f"Transcription received for call {call_sid}")
        logger.debug(f"Transcription preview: {transcription_text[:100]}...")
        
        # Store transcript in session
        session['transcript'] = transcription_text
        
        # Get DTMF sequence from session
        dtmf_sequence = session.get('dtmf_sequence', [])
        
        # Generate flowchart from transcription
        flowchart = generate_flowchart(transcription_text)
        
        # Perform analytics
        analytics = IVRAnalytics(transcription_text, flowchart)
        metrics = analytics.get_metrics()
        summary = analytics.get_summary()
        visualization_data = analytics.get_visualization_data()
        
        # Store analysis results
        analysis_results = {
            'transcript': transcription_text,
            'flowchart': flowchart,
            'metrics': metrics,
            'summary': summary,
            'visualization_data': visualization_data,
            'dtmf_sequence': dtmf_sequence,
            'timestamp': time.time()
        }
        
        # Store in session
        session[f'analysis_{call_sid}'] = analysis_results
        
        # Store in global latest analysis
        global latest_analysis
        latest_analysis = analysis_results
        
        logger.info("IVR analysis completed successfully")
        logger.debug(f"Analysis results: {json.dumps(analysis_results, indent=2)}")
        
        # End the call if it's still active
        response = VoiceResponse()
        response.say("Analysis complete. Thank you for your call.",
                    voice='alice',
                    language='en-US')
        response.hangup()
        
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error processing transcription: {str(e)}", exc_info=True)
        error_response = VoiceResponse()
        error_response.hangup()
        return Response(str(error_response), mimetype='text/xml')

if __name__ == '__main__':
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        logger.critical("OPENAI_API_KEY not set in environment variables")
        print("ERROR: OPENAI_API_KEY not set. Please set it in your .env file.")
        exit(1)
    
    # Get port from environment variable (for cloud platforms)
    port = int(os.getenv('PORT', 5000))
    
    # Use environment variable to control debug mode
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    logger.info(f"Starting app on port {port} with debug={debug_mode}")
    
    # Run the application
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

    
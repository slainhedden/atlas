import os
import pathlib
from flask import Flask, request, jsonify
from utility.screenshot_handler import ScreenshotHandler
from llm.ai_handler import AIAssistant
import threading
import queue
import time
from utility.audio_handler import AudioRecorder

app = Flask(__name__)

# Initialize ScreenshotHandler
screenshot_handler = ScreenshotHandler(max_screenshots=15, compression_quality=85)

ai_assistant = AIAssistant()
audio_recorder = AudioRecorder()

@app.route('/api/start_recording', methods=['POST'])
def start_recording():
    status = audio_recorder.start_recording()
    return jsonify({'status': status})

@app.route('/api/stop_recording', methods=['POST'])
def stop_recording():
    audio_file = audio_recorder.stop_recording()
    if audio_file == "Not recording":
        return jsonify({'result': 'Error: Not recording'})
    else:
        screenshots = screenshot_handler.screenshot_memory()
        transcription = audio_recorder.transcribe_audio(screenshots, audio_file)
        return jsonify({'result': transcription})

###########################################
# Depricated for now --- Will be used in future
# @app.route('/api/transcribe', methods=['POST'])
# def transcribe_audio():
#     data = request.json
#     audio_file = data.get('audio_file')
#     if not audio_file:
#         return jsonify({'error': 'No audio file provided'}), 400
#
#     transcription = audio_recorder.transcribe_audio(audio_file)
#     return jsonify({'transcription': transcription.text})
###########################################
    
@app.route('/api/query', methods=['POST'])
def process_query():
    data = request.json
    query = data.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    # Get the latest screenshots
    screenshots = screenshot_handler.screenshot_memory()

    ai_assistant.process_query(query, screenshots)
    
    # Wait for the response (you might want to implement a timeout mechanism)
    response = None
    while response is None:
        response = ai_assistant.get_response()
    
    return jsonify({'response': response})

@app.route('/api/screenshot', methods=['POST'])
def capture_screenshot():
    filepath = screenshot_handler.capture_screenshot()
    return jsonify({'filepath': filepath})

@app.route('/api/screenshot/settings', methods=['GET', 'POST'])
def screenshot_settings():
    if request.method == 'POST':
        data = request.json
        interval = data.get('interval')
        if interval is not None:
            # Update the screenshot interval (you'll need to implement this in ScreenshotHandler)
            screenshot_handler.set_interval(interval)
        return jsonify({'status': 'success'})
    else:
        # Get current settings (you'll need to implement this in ScreenshotHandler)
        settings = screenshot_handler.get_settings()
        return jsonify(settings)

@app.route('/api/chat/save', methods=['POST'])
def save_chat():
    data = request.json
    chat_content = data.get('content')
    if not chat_content:
        return jsonify({'error': 'No chat content provided'}), 400
    
    filename = f"chat_{int(time.time())}.txt"
    with open(filename, "w") as f:
        f.write(chat_content)
    
    return jsonify({'filename': filename})

@app.route('/api/chat/closed', methods=['POST'])
def clear_images():
    screenshot_handler.cleanup()
    return jsonify({'status': 'success'})
    
if __name__ == '__main__':
    app.run(port=5000, debug=True)

import pyaudio
import wave
import os
import time
from pydub import AudioSegment
from openai import OpenAI
from config.keys import API_KEYS
from llm.ai_handler import AIAssistant
import threading
import pathlib
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key=API_KEYS.GEMINI)
model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat(history=[])

class AudioRecorder:
    def __init__(self, chunk=1024, format=pyaudio.paInt16, channels=1, rate=44100):
        self.chunk = chunk
        self.format = format
        self.channels = channels
        self.rate = rate
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.openai_client = OpenAI(api_key=API_KEYS.OPENAPI)

    def start_recording(self):
        if self.is_recording:
            return "Already recording"

        self.stream = self.audio.open(format=self.format, channels=self.channels,
                                      rate=self.rate, input=True,
                                      frames_per_buffer=self.chunk)
        self.frames = []
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record_loop)
        self.recording_thread.start()
        return "Recording started"

    def stop_recording(self):
        if not self.is_recording:
            return "Not recording"

        self.is_recording = False
        self.recording_thread.join()
        
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except OSError:
                print("Error stopping stream")

        # Save as WAV
        timestamp = int(time.time())
        wav_filename = f"recording_{timestamp}.wav"
        wf = wave.open(wav_filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()

        return wav_filename

    def _record_loop(self):
        while self.is_recording:
            self.record_frame()
            time.sleep(0.01)  # Adjust sleep time as needed

    def record_frame(self):
        if self.is_recording:
            data = self.stream.read(self.chunk)
            self.frames.append(data)

    def transcribe_audio(self, images, audio_file):
        try:
            with open(audio_file, "rb") as file:
                if os.path.getsize(audio_file) == 0:
                    return "Error: Empty audio file"
                transcription = self.openai_client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=file,
                    response_format="text"
                )

            prompt = f"The user has asked the following question: {transcription}\nHere are the last screenshots of their screen for context. Please analyze these images and provide a helpful response."
            
            image_data = []
            for path in images:
                image_data.append({
                    'mime_type': 'image/png',
                    'data': pathlib.Path(path).read_bytes()
                })

            response = chat.send_message([prompt] + image_data)
            return response.text
        except Exception as e:
            print(f"Error in transcribe_audio: {str(e)}")
            return f"Error transcribing audio: {str(e)}"

    def cleanup(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()

    def _remove_audio_file(self, filepath):
        try:
            os.remove(filepath)
        except OSError as e:
            print(f"Error removing audio file {filepath}: {e}")
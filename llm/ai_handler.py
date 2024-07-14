import queue
import threading
import pathlib
from config.keys import API_KEYS
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key=API_KEYS.GEMINI)
model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat(history=[])

class AIAssistant:
    def __init__(self):
        self.query_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.processing_thread = threading.Thread(target=self._process_queries, daemon=True)
        self.processing_thread.start()

    def _process_queries(self):
        while True:
            query, screenshot_paths = self.query_queue.get()
            if query is None:
                break
            response = self._generate_response(query, screenshot_paths)
            self.response_queue.put(response)

    def _generate_response(self, query, screenshot_paths):
        images = []
        for path in screenshot_paths:
            images.append({
                'mime_type': 'image/png',
                'data': pathlib.Path(path).read_bytes()
            })
        
        prompt = f"{query}\nHere are the last screenshots of their screen for context. Please analyze these images and provide a helpful response."
        
        response = chat.send_message([prompt] + images)
        return response.text

    def process_query(self, query, screenshot_paths):
        self.query_queue.put((query, screenshot_paths))

    def get_response(self):
        try:
            return self.response_queue.get_nowait()
        except queue.Empty:
            return None
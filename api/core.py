import os
import pathlib
import threading
import queue
import time
from pydantic import BaseModel

# Fast API imports
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

# Utility imports
from utility.audio_handler import AudioRecorder
from utility.codebase_handler import CodeHelper
from utility.screenshot_handler import ScreenshotHandler
from llm.ai_handler import AIAssistant


app = FastAPI()

# Initialize ScreenshotHandler
screenshot_handler = ScreenshotHandler(max_screenshots=15, compression_quality=85)
ai_assistant = AIAssistant()
audio_recorder = AudioRecorder()
code_helper = CodeHelper()

class Query(BaseModel):
    query: str
    # This class defines the structure of the data expected when a user sends a query to our API.
    
class ChatContent(BaseModel):
    content: str
    # This class defines the structure of the datra expected when saving chat content

class ScreenshotSettings(BaseModel):
    interval: int = None
    # This class defines the structure of the data expected when updating screenshot settings
    
'''
These classes are used for:
1. Validation: When a request is made to your FastAPI endpoints that use these models, FastAPI automatically validates the 
incoming request data against these models. if the data does not match the expected format or types, FastAPI will return a
422 Unprocessable Entity response.
2. Type Safety: These models provide type hints, which help with code readability and type checking in IDEs.
3. Data Parsing: The models parse and convert incoming JSON data into Python objects, making it easier to work with the data in your endpoint
functions.
'''

# Create a feature that screenshots the current screen that we are working on currently

@app.get("/")
async def root():
    # Take a screenshot immediately when the application starts.
    return {"message": "Welcome to the FastAPI application"}

@app.post("/api/start_recording")
async def start_recording():
    status = audio_recorder.start_recording()
    return JSONResponse(content={'status': status})

@app.post("/api/stop_recording")
async def stop_recording():
    audio_file = audio_recorder.stop_recording()
    if audio_file == "Not recording":
        raise HTTPException(status_code=400, detail='Error: Not recording')
    else:
        screenshots = screenshot_handler.screenshot_memory()
        transcription = audio_recorder.transcribe_audio(screenshots, audio_file)
        return JSONResponse(content={'result': transcription})

@app.post("/api/query")
async def process_query(query: Query):
    if not query.query:
        raise HTTPException(status_code=400, detail='No query provided')

    # Get the latest screenshots
    screenshots = screenshot_handler.screenshot_memory()

    ai_assistant.process_query(query.query, screenshots)
    
    # Wait for the response (you might want to implement a timeout mechanism)
    response = None
    while response is None:
        response = ai_assistant.get_response()
    
    return JSONResponse(content={'response': response})

@app.post("/api/code_query")
async def process_code_query(query: Query):
    if not query.query:
        raise HTTPException(status_code=400, detail='No path provided')

    try:
        codebase_content = code_helper.analyze_codebase(query.query)
        print(f"Codebase content length: {len(codebase_content)}")  # Add this line for debugging
        prompt = f"Analyze the following codebase and provide insights or answer questions about it:\n\n{codebase_content}"
        
        ai_assistant.process_query(prompt, [])
        
        response = None
        timeout = 30  # Set a timeout of 30 seconds
        start_time = time.time()
        while response is None and time.time() - start_time < timeout:
            response = ai_assistant.get_response()
            if response is None:
                await asyncio.sleep(0.5)
        
        if response is None:
            raise TimeoutError("AI assistant did not respond in time")
        
        return JSONResponse(content={'response': response})
    except Exception as e:
        print(f"Error in process_code_query: {str(e)}")
        raise HTTPException(status_code=500, detail=f'Error processing code query: {str(e)}')


@app.post("/api/screenshot")
async def capture_screenshot():
    filepath = screenshot_handler.capture_screenshot()
    return JSONResponse(content={'filepath': filepath})

@app.get("/api/screenshot/settings")
async def get_screenshot_settings():
    settings = screenshot_handler.get_settings()
    return JSONResponse(content=settings)

@app.post("/api/screenshot/settings")
async def update_screenshot_settings(settings: ScreenshotSettings):
    if settings.interval is not None:
        # Update the screenshot interval (you'll need to implement this in ScreenshotHandler)
        screenshot_handler.set_interval(settings.interval)
    return JSONResponse(content={'status': 'success'})

@app.post("/api/chat/save")
async def save_chat(chat_content: ChatContent):
    if not chat_content.content:
        raise HTTPException(status_code=400, detail='No chat content provided')
    
    filename = f"chat_{int(time.time())}.txt"
    with open(filename, "w") as f:
        f.write(chat_content.content)
    
    return JSONResponse(content={'filename': filename})

@app.post("/api/chat/closed")
async def clear_images():
    screenshot_handler.cleanup()
    return JSONResponse(content={'status': 'success'})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

    
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

const { app, BrowserWindow, ipcMain } = require('electron'); // Downloads and installs the necessary packages for creating and managing electron apps
const path = require('path'); 
const axios = require('axios'); // For making HTTP requests to Flask Backend

let mainWindow;
const FLASK_URL = 'http://127.0.0.1:5000/';

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    mainWindow.loadFile('src/renderer/index.html');

    mainWindow.on('closed', function () {
        mainWindow = null;
    });

    // Handle query requests from renderer
    ipcMain.on('query', async (event, query) => {
        try {
            const response = await axios.post(`${FLASK_URL}/api/query`, { query });
            event.reply('queryResponse', response.data.response);
        } catch (error) {
            console.error('Error querying AI:', error);
            event.reply('queryResponse', 'Error: Unable to get response from AI');
        }
    });

    // Handle screenshot capture requests from renderer
    ipcMain.on('captureScreenshot', async (event) => {
        try {
            const response = await axios.post(`${FLASK_URL}/api/screenshot`);
            event.reply('screenshotCaptured', response.data.filepath);
        } catch (error) {
            console.error('Error capturing screenshot:', error);
            event.reply('screenshotCaptured', 'Error: Unable to capture screenshot');
        }
    });

    // Handle start recording request
    ipcMain.on('startRecording', async (event) => {
        try {
            const response = await axios.post(`${FLASK_URL}/api/start_recording`);
            event.reply('recordingStarted', response.data.status);
        } catch (error) {
            console.error('Error starting recording:', error);
            event.reply('recordingStarted', 'Error: Unable to start recording');
        }
    });

    // Handle stop recording request
    ipcMain.on('stopRecording', async (event) => {
        try {
            const response = await axios.post(`${FLASK_URL}/api/stop_recording`); //calls flask endpoint in python
            event.reply('recordingStopped', response.data.result); // sends the response back to the renderer
        } catch (error) {
            console.error('Error stopping recording:', error);
            event.reply('recordingStopped', 'Error: Unable to stop recording');
        }
    });

}
    
let screenshotInterval;

function startScreenshotCapture() {
    screenshotInterval = setInterval(async () => {
        try {
            const response = await axios.post(`${FLASK_URL}/api/screenshot`);
            console.log('Screenshot captured:', response.data.filepath);
        } catch (error) {
            console.error('Error capturing screenshot:', error);
        }
    }, 5000);
}

function stopScreenshotCapture() {
    clearInterval(screenshotInterval);
    axios.post(`${FLASK_URL}/api/chat/closed`)
        .then(() => console.log('Screenshots cleared'))
        .catch(error => {
            console.error('Error clearing screenshots:', error);
            // Optionally, you can notify the renderer process about this error
        });
}

app.on('ready', () => {
    createWindow();
    startScreenshotCapture();
});

app.on('will-quit', () => {
    stopScreenshotCapture();
});

app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', function () {
    if (mainWindow === null) {
        createWindow();
    }  
});
const { ipcRenderer } = require('electron');

document.getElementById('sendButton').addEventListener('click', () => {
    const userInput = document.getElementById('queryInput').value;
    if (userInput) {
        ipcRenderer.send('toPython', { query: userInput, screenshot_paths: [] }); // Update according to how screenshots are handled
    }
});

ipcRenderer.on('fromPython', (event, message) => {
    document.getElementById('responseArea').innerText = 'Response: ' + message;
});
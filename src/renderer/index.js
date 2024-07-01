const { ipcRenderer } = require('electron');

document.addEventListener('DOMContentLoaded', () => {
    const queryInput = document.getElementById('queryInput');
    const sendQueryBtn = document.getElementById('sendQuery');
    const voiceQueryBtn = document.getElementById('voiceQuery');
    const chatWindow = document.getElementById('chatWindow');

    function addMessageToChatWindow(sender, message) {
        const messageElement = document.createElement('div');
        messageElement.className = `mb-4 p-3 rounded-lg ${
            sender === 'AI' 
                ? 'bg-blue-900 text-blue-100 ml-4' 
                : sender === 'You' 
                    ? 'bg-green-900 text-green-100 mr-4' 
                    : 'bg-gray-700 text-gray-100'
        }`;
        messageElement.innerHTML = `<strong class="font-bold">${sender}:</strong> ${message}`;
        chatWindow.appendChild(messageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    sendQueryBtn.addEventListener('click', sendQuery);
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendQuery();
    });

    function sendQuery() {
        const query = queryInput.value.trim();
        if (query) {
            addMessageToChatWindow('You', query);
            ipcRenderer.send('query', query);
            queryInput.value = '';
        }
    }

    let isRecording = false;
    voiceQueryBtn.addEventListener('click', () => {
        if (!isRecording) {
            isRecording = true;
            ipcRenderer.send('startRecording');
            voiceQueryBtn.classList.remove('bg-green-500', 'hover:bg-green-600');
            voiceQueryBtn.classList.add('bg-red-500', 'hover:bg-red-600', 'animate-pulse');
        } else {
            ipcRenderer.send('stopRecording');
            isRecording = false;
            voiceQueryBtn.classList.remove('bg-red-500', 'hover:bg-red-600', 'animate-pulse');
            voiceQueryBtn.classList.add('bg-green-500', 'hover:bg-green-600');
            voiceQueryBtn.querySelector('svg').classList.remove('animate-pulse');
        }
    });

    ipcRenderer.on('recordingStarted', (event, status) => {
        if (status !== "Already recording") {
            addMessageToChatWindow('System', 'Recording started. Speak now...');
        }
    });

    ipcRenderer.on('queryResponse', (event, response) => {
        addMessageToChatWindow('AI', response);
    });

    ipcRenderer.on('recordingStopped', (event, result) => {
        if (result.startsWith('Error')) {
            addMessageToChatWindow('System', result);
        } else {
            ipcRenderer.send('query', result); // Send the transcribed text as a query
        }
    });

    ipcRenderer.on('transcription', (event, transcription) => {
        addMessageToChatWindow('AI', transcription);
        ipcRenderer.send('query', transcription); // Send the transcribed text as a query
    });
});
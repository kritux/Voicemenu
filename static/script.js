const recordBtn = document.getElementById('record-btn');
const transcriptDiv = document.getElementById('transcript');
const orderResultDiv = document.getElementById('order-result');

let mediaRecorder;
let audioChunks = [];

function speak(text) {
    const synth = window.speechSynthesis;
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = 'en-US';
    synth.speak(utter);
}

function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };
            
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const reader = new FileReader();
                reader.onload = () => {
                    // Enviar audio al backend para transcripción
                    fetch('/transcribe_audio', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ audio: reader.result })
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.error) {
                            transcriptDiv.textContent = 'Error: ' + data.error;
                        } else {
                            const text = data.text;
                            transcriptDiv.textContent = 'You said: ' + text;
                            // Enviar texto al backend para procesar orden
                            processOrder(text);
                        }
                    })
                    .catch(() => {
                        transcriptDiv.textContent = 'Error transcribing audio.';
                    });
                };
                reader.readAsDataURL(audioBlob);
            };
            
            mediaRecorder.start();
            recordBtn.textContent = '🛑 Stop Recording';
            transcriptDiv.textContent = 'Listening... Speak your complete order (pizza, size, and drink)';
        })
        .catch(err => {
            transcriptDiv.textContent = 'Error accessing microphone: ' + err.message;
        });
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        recordBtn.textContent = '🎤 Start Order';
    }
}

function processOrder(text) {
    orderResultDiv.textContent = 'Processing your order...';
    
    fetch('/process_order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: text })
    })
    .then(res => res.json())
    .then(data => {
        orderResultDiv.textContent = data.message;
        speak(data.message.replace(/\n/g, '. '));
    })
    .catch(() => {
        orderResultDiv.textContent = 'Error processing order.';
    });
}

recordBtn.onclick = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        stopRecording();
    } else {
        startRecording();
    }
}; 
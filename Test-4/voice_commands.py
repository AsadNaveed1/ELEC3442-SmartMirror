from flask import Flask, jsonify, request
from flask_cors import CORS
import speech_recognition as sr
import threading
import time
import queue

app = Flask(__name__)
CORS(app)

command_queue = queue.Queue(maxsize=1)

VALID_COMMANDS = [
    "show weather", "weather", "show me the weather", "what's the weather",
    "show calendar", "calendar", "show me the calendar", "schedule", "show schedule", "show me the schedule",
    "show outfit", "outfit", "show me the outfit", "clothes", "what should i wear",
    "show music", "music", "play music", "show me music recommendations",
    "face recognition", "recognize face", "emotion", "how do i look",
    "accessories", "show accessories", "virtual accessories",
    "close", "stop", "exit", "turn off"
]

def recognize_speech():
    """Continuously recognizes speech and puts commands in the queue"""
    recognizer = sr.Recognizer()
    
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 4000
    recognizer.pause_threshold = 0.8
    
    print("Voice recognition service started")
    
    while True:
        try:
            with sr.Microphone() as source:
                print("Listening for commands...")
                audio = recognizer.listen(source, phrase_time_limit=5)
                print("Processing audio...")
                
                try:
                    text = recognizer.recognize_google(audio).lower()
                    print(f"Recognized: {text}")
                    
                    command_added = False
                    for command in VALID_COMMANDS:
                        if command in text:
                            if command_queue.full():
                                try:
                                    command_queue.get_nowait()
                                except queue.Empty:
                                    pass
                            
                            command_queue.put(command)
                            print(f"Command added to queue: {command}")
                            command_added = True
                            break
                    
                    if not command_added:
                        key_terms = ["weather", "calendar", "schedule", "outfit", "clothes", 
                                    "music", "play", "face", "emotion", "accessories"]
                        
                        for term in key_terms:
                            if term in text:
                                if command_queue.full():
                                    try:
                                        command_queue.get_nowait()
                                    except queue.Empty:
                                        pass
                                
                                command_queue.put(text)
                                print(f"Added full text as command: {text}")
                                break
                    
                except sr.UnknownValueError:
                    print("Could not understand audio")
                except sr.RequestError as e:
                    print(f"Could not request results from Google Speech Recognition service; {e}")
        
        except Exception as e:
            print(f"Error in voice recognition: {e}")
        
        time.sleep(0.1)

@app.route('/voice', methods=['GET'])
def get_voice_command():
    """API endpoint to get the latest voice command"""
    try:
        try:
            command = command_queue.get_nowait()
            return jsonify({
                "status": "success",
                "command": command
            })
        except queue.Empty:
            return jsonify({
                "status": "no_command",
                "message": "No voice command detected"
            })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/status', methods=['GET'])
def get_status():
    """API endpoint to check if the voice service is running"""
    return jsonify({
        "status": "running",
        "service": "voice_recognition"
    })

if __name__ == "__main__":
    threading.Thread(target=recognize_speech, daemon=True).start()
    
    app.run(debug=False, port=5005, host='0.0.0.0')
from flask import Flask, jsonify, request
from flask_cors import CORS
import speech_recognition as sr
import threading
import time
import queue

app = Flask(__name__)
CORS(app)

# Queue to store the latest recognized command
command_queue = queue.Queue(maxsize=1)

# Available commands
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
    
    # Adjust for ambient noise levels
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 4000  # Higher threshold to avoid false triggers
    recognizer.pause_threshold = 0.8    # Shorter pause to detect end of phrases quickly
    
    print("Voice recognition service started")
    
    while True:
        try:
            with sr.Microphone() as source:
                # Listen for the first phrase and extract it into audio data
                print("Listening for commands...")
                audio = recognizer.listen(source, phrase_time_limit=5)
                print("Processing audio...")
                
                try:
                    # Use Google Speech Recognition to convert audio to text
                    text = recognizer.recognize_google(audio).lower()
                    print(f"Recognized: {text}")
                    
                    # Check if the recognized text contains any valid command
                    command_added = False
                    for command in VALID_COMMANDS:
                        if command in text:
                            # If command queue is full, remove the old command
                            if command_queue.full():
                                try:
                                    command_queue.get_nowait()
                                except queue.Empty:
                                    pass
                            
                            # Add the new command to the queue
                            command_queue.put(command)
                            print(f"Command added to queue: {command}")
                            command_added = True
                            break
                    
                    # If no exact command match, use the full text if it contains key terms
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
                                
                                command_queue.put(text)  # Put the entire text as the command
                                print(f"Added full text as command: {text}")
                                break
                    
                except sr.UnknownValueError:
                    # Speech was unintelligible
                    print("Could not understand audio")
                except sr.RequestError as e:
                    # Could not request results from Google Speech Recognition service
                    print(f"Could not request results from Google Speech Recognition service; {e}")
        
        except Exception as e:
            print(f"Error in voice recognition: {e}")
        
        # Small delay to prevent CPU overuse
        time.sleep(0.1)

@app.route('/voice', methods=['GET'])
def get_voice_command():
    """API endpoint to get the latest voice command"""
    try:
        # Try to get a command from the queue, don't wait if empty
        try:
            command = command_queue.get_nowait()
            return jsonify({
                "status": "success",
                "command": command
            })
        except queue.Empty:
            # No command available
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
    # Start the speech recognition in a separate thread
    threading.Thread(target=recognize_speech, daemon=True).start()
    
    # Run the Flask app
    app.run(debug=False, port=5005, host='0.0.0.0')
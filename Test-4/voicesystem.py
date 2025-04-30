import speech_recognition as sr
from flask import Flask, jsonify
from flask_cors import CORS
import threading
import time

app = Flask(__name__)
CORS(app)  # Allow CORS for localhost

# Global variable to store the latest recognized command
latest_command = {"status": "idle", "command": "", "message": ""}

# Lock to prevent race conditions when accessing latest_command
command_lock = threading.Lock()

def recognize_speech():
    """Capture and recognize speech from the microphone."""
    global latest_command
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 4000
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.5

    with sr.Microphone() as source:
        print("Listening for voice command...")
        recognizer.adjust_for_ambient_noise(source, duration=5)
        try:
            audio = recognizer.listen(source, timeout=100, phrase_time_limit=3)
            print("Processing voice input...")
            text = recognizer.recognize_google(audio).lower()
            print(f"Recognized: {text}")
            with command_lock:
                latest_command = {"status": "success", "command": text, "message": ""}
            return latest_command
        except sr.WaitTimeoutError:
            with command_lock:
                latest_command = {"status": "idle", "message": "No speech detected"}
            return latest_command
        except sr.UnknownValueError:
            with command_lock:
                latest_command = {"status": "error", "message": "Could not understand the speech"}
            return latest_command
        except sr.RequestError as e:
            with command_lock:
                latest_command = {"status": "error", "message": f"Speech recognition error: {e}"}
            return latest_command

def continuous_recognition():
    """Run speech recognition in a loop to continuously listen."""
    while True:
        recognize_speech()
        time.sleep(0.5)  # Short pause for responsiveness

@app.route('/voice', methods=['GET'])
def get_voice_command():
    """Return the latest recognized voice command and reset it."""
    global latest_command
    with command_lock:
        response = latest_command
        # Reset to idle state if a command was sent
        if response["status"] == "success" and response["command"]:
            latest_command = {"status": "idle", "command": "", "message": "Command processed"}
    return jsonify(response)

if __name__ == "__main__":
    # Start continuous speech recognition in a separate thread
    recognition_thread = threading.Thread(target=continuous_recognition, daemon=True)
    recognition_thread.start()
    # Run Flask server
    print("Starting voice recognition service on port 5004...")
    app.run(host='0.0.0.0', port=5004, debug=False)
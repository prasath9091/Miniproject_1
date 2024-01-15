import requests
from datetime import datetime, timedelta
import speech_recognition as sr
import pyttsx3
import sqlite3
import os

# Initialize pyttsx3
engine = pyttsx3.init()

# Set your AssemblyAI API key
assemblyai_api_key = "a938ad6c3b98448f8ed1a872016e65dd"

# Get the current script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# SQLite database setup in the same directory
db_file = "database.db"
db_path = os.path.join(script_dir, db_file)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create events table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_name TEXT,
        event_time TEXT,
        event_month TEXT
    )
''')
conn.commit()

def get_response_from_assemblyai(audio_data):
    url = "https://api.assemblyai.com/v2/realtime/stream"

    headers = {
        "authorization": assemblyai_api_key,
        "content-type": "application/json",
    }

    data = {
        "audio_channel": "1",
        "sample_rate": 44100,
        "language_model": "assemblyai_model",
    }

    response = requests.post(url, json=data, headers=headers, stream=True)

    if response.status_code == 200:
        for chunk in audio_data:
            response = requests.post(url, data=chunk, headers=headers)
        result = response.json()
        return result.get("text", "Error with AssemblyAI API")
    else:
        print(f"Error with AssemblyAI API: {response.text}")
        return "Error with AssemblyAI API"

def store_event_in_database(event_name, event_time, event_month):
    cursor.execute("INSERT INTO events (event_name, event_time, event_month) VALUES (?, ?, ?)",
                   (event_name, event_time, event_month))
    conn.commit()

def schedule_event(event_name, event_time, event_month):
    current_year = datetime.now().year
    event_date_str = f"{event_month} {event_time} {current_year}"
    event_date = datetime.strptime(event_date_str, "%B %d %I %p %Y")

    alert_time = event_date - timedelta(minutes=15)

    store_event_in_database(event_name, event_time, event_month)

    print(f"Event scheduled: {event_name} at {event_time} on {event_month}")

    return alert_time

def alert_user(event_name, event_time):
    print(f"Event alert: {event_name} at {event_time}")
    engine.say(f"Event alert: {event_name} at {event_time}")
    engine.runAndWait()

def check_scheduled_events():
    try:
        cursor.execute("SELECT * FROM events ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()

        if row:
            event_name, event_time, event_month = row[1], row[2], row[3]
            event_datetime = datetime.strptime(event_time, "%Y-%m-%dT%H:%M:%SZ")

            now = datetime.now()
            if now >= event_datetime:
                alert_user(event_name, event_time)
                print(f"Scheduled event arrived: {event_name} at {event_time}")

            return event_name, event_time

    except Exception as e:
        print(f"Error checking scheduled events: {e}")

def recognize_and_respond():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        recognizer.dynamic_energy_threshold = 3000

        while True:
            try:
                print("Listening... ")
                audio_data = recognizer.listen(source, timeout=5.0, phrase_time_limit=10)
                
                spoken_text = recognizer.recognize_google(audio_data)
                print(spoken_text)

                if "jarvis" in spoken_text.lower():
                    print(f"Recognized text: {spoken_text}")

                    if "can you hear me" in spoken_text.lower():
                        engine.say("Yes, I can hear you.")
                        engine.runAndWait()
                    else:
                        response_from_assemblyai = get_response_from_assemblyai(audio_data)

                        print(f"Assistant's Response: {response_from_assemblyai}")
                        engine.say(response_from_assemblyai)
                        engine.runAndWait()

                        event_name, event_time, event_month = parse_spoken_text(response_from_assemblyai)

                        if event_name and event_time and event_month:
                            schedule_event(event_name, event_time, event_month)
                        else:
                            print("Failed to parse event details.")

                # Continuous checking for scheduled events
                event_details = check_scheduled_events()

            except sr.UnknownValueError:
                print("Didn't recognize anything.")
            except sr.RequestError as e:
                print(f"Error with the Google Speech Recognition service: {e}")

if __name__ == "__main__":
    recognize_and_respond()

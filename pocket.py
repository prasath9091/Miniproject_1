import os
from datetime import datetime, timedelta
import speech_recognition as sr
import pyttsx3
import sqlite3
import dateutil.parser
from pocketsphinx import LiveSpeech

# Initialize pyttsx3
engine = pyttsx3.init()

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

def extract_time_and_month(text):
    try:
        # Use dateutil.parser.parse for flexible parsing
        parsed_date = dateutil.parser.parse(text, fuzzy=True)
        
        # Format the parsed date as strings
        formatted_time = parsed_date.strftime("%I:%M %p")
        formatted_month = parsed_date.strftime("%B")

        return formatted_time, formatted_month
    except ValueError:
        # Handle parsing errors
        print("Error: Unable to parse date and time from the input.")
        return None, None

def parse_spoken_text(spoken_text):
    # Improved logic for broader natural language understanding
    event_name = None
    event_time = None
    event_month = None

    if "schedule" in spoken_text.lower() or "remind me to" in spoken_text.lower():
        parts = spoken_text.lower().split("on")
        if len(parts) == 2:
            event_name = parts[0].strip()
            time, month = extract_time_and_month(parts[1].strip())
            if time and month:
                event_time = time
                event_month = month

    return event_name, event_time, event_month

def store_event_in_database(event_name, event_time, event_month):
    cursor.execute("INSERT INTO events (event_name, event_time, event_month) VALUES (?, ?, ?)",
                   (event_name, event_time, event_month))
    conn.commit()

def schedule_event(event_name, event_time, event_month):
    current_year = datetime.now().year
    event_date_str = f"{event_month} {event_time} {current_year}"
    event_date = datetime.strptime(event_date_str, "%B %d %I:%M %p %Y")

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

        # Adjusted to use CMU Sphinx (pocketsphinx)
        for phrase in LiveSpeech():
            try:
                spoken_text = str(phrase)
                print(spoken_text)

                if "jarvis" in spoken_text.lower():
                    print(f"Recognized text: {spoken_text}")

                    if "can you hear me" in spoken_text.lower():
                        engine.say("Yes, I can hear you.")
                        engine.runAndWait()
                    else:
                        event_name, event_time, event_month = parse_spoken_text(spoken_text)

                        if event_name and event_time and event_month:
                            response = f"Scheduled: {event_name} at {event_time} on {event_month}"
                            engine.say(response)
                            engine.runAndWait()

                            alert_time = schedule_event(event_name, event_time, event_month)

                            # Continuous checking for scheduled events
                            event_details = check_scheduled_events()

                            if event_details:
                                response = f"Scheduled event arrived: {event_details[0]} at {event_details[1]}"
                                engine.say(response)
                                engine.runAndWait()
                        else:
                            print("Failed to parse event details.")

            except sr.UnknownValueError:
                print("Didn't recognize anything.")
            except sr.RequestError as e:
                print(f"Error with the Google Speech Recognition service: {e}")

if __name__ == "__main__":
    recognize_and_respond()

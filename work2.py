import requests
from datetime import datetime, timedelta
import speech_recognition as sr
import pyttsx3
import sqlite3
import os
import dateutil.parser

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
        event_month TEXT,
        event_date TEXT
    )
''')
conn.commit()


def extract_time_and_month(text):
    try:
        parsed_date = dateutil.parser.parse(text, fuzzy=True)
        return parsed_date.strftime("%I:%M %p"), parsed_date.strftime("%B")
    except ValueError:
        print("Error parsing date and time.")
        return None, None



def parse_spoken_text(spoken_text):
    event_name = "default_event_name"
    event_time, event_month = extract_time_and_month(spoken_text)

    if "remind me to" in spoken_text.lower():
        event_name = spoken_text.lower().split("remind me to")[1].strip()
    elif "schedule a meeting" in spoken_text.lower():
        event_name = "meeting"  # Placeholder, you can extract more details here if needed

    return event_name, event_time, event_month


def store_event_in_database(event_name, event_time, event_month, event_date):
    cursor.execute("INSERT INTO events (event_name, event_time, event_month, event_date) VALUES (?, ?, ?, ?)",
                   (event_name, event_time, event_month, event_date))
    conn.commit()

def schedule_event(event_name, event_time, event_month):
    current_year = datetime.now().year

    # Check if day is provided in event_time
    if " " in event_time:
        event_date_str = f"{event_month} {event_time} {current_year}"
    else:
        # Assuming the event is scheduled for the 1st day of the month if no day is provided
        event_date_str = f"{event_month} 1 {event_time} {current_year}"

    try:
        # Use dateutil.parser.parse for flexible parsing
        event_datetime = dateutil.parser.parse(event_date_str, fuzzy=True)
    except ValueError:
        print(f"Failed to parse event details: {event_name} at {event_time} on {event_month}")
        return None

    alert_time = event_datetime - timedelta(minutes=15)

    store_event_in_database(event_name, event_time, event_month, alert_time.date())  # Updated line

    print(f"Event scheduled: {event_name} at {event_time} on {event_month}")

    return alert_time



def alert_user(event_name, event_time, event_date):
    print(f"Event alert: {event_name} at {event_time} on {event_date}")
    engine.say(f"Event alert: {event_name} at {event_time} on {event_date}")
    engine.runAndWait()

def check_scheduled_events():
    try:
        cursor.execute("SELECT * FROM events ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()

        if row:
            event_name, event_time, event_month, event_date = row[1], row[2], row[3], row[4]

            # Convert month name to a numeric month
            month_number = datetime.strptime(event_month, "%B").month

            # Format the date explicitly
            formatted_date = f"{event_date}-{month_number:02d}"

            event_datetime = dateutil.parser.parse(f"{formatted_date} {event_time}")

            now = datetime.now()
            if now.date() == event_datetime.date() and now >= event_datetime:
                alert_user(event_name, event_time, event_date)
                print(f"Scheduled event arrived: {event_name} at {event_time} on {event_date}")

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
                audio_data = recognizer.listen(source, timeout=None)

                spoken_text = recognizer.recognize_google(audio_data)
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

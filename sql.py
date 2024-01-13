import sqlite3
import requests
from datetime import datetime, timedelta
import pyttsx3
import speech_recognition as sr
import openai

# Initialize pyttsx3
engine = pyttsx3.init()

# Set your OpenAI API key and customize the ChatGPT role
openai.api_key = ""
messages = [{"role": "system", "content": "Your name is Jarvis and give answers in 2 lines"}]

# SQLite database connection
sqlite_connection = sqlite3.connect('events.db')
sqlite_cursor = sqlite_connection.cursor()

def send_to_database(event_name, event_time):
    try:
        # Create a table if not exists
        sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS events
                                (name TEXT, time TEXT)''')

        # Insert event data
        sqlite_cursor.execute('INSERT INTO events VALUES (?, ?)', (event_name, event_time))

        # Commit changes
        sqlite_connection.commit()

        print(f"Event '{event_name}' sent to SQLite database successfully.")
    except Exception as e:
        print(f"Error sending event '{event_name}' to SQLite database: {e}")

def parse_spoken_text(spoken_text):
    # Basic example: "Schedule meeting at 3 PM on November 15th"
    # Extract event name, time, and month from spoken text
    # Modify this based on your specific requirements

    # Assuming time is mentioned in the format "at [time] on [month] [day]"
    time_index = spoken_text.find("at")
    on_index = spoken_text.find("on")

    if time_index != -1 and on_index != -1:
        event_name = spoken_text[9:time_index - 1]
        event_time = spoken_text[time_index + 3:on_index - 1]
        event_month = spoken_text[on_index + 3:]

        return event_name, event_time, event_month

    return None, None, None  # Invalid input

def schedule_event(event_name, event_time, event_month):
    # Add your scheduling logic here
    # This is a placeholder, modify based on your project requirements
    current_year = datetime.now().year
    event_date_str = f"{event_month} {event_time} {current_year}"
    event_date = datetime.strptime(event_date_str, "%B %d %I %p %Y")

    # Assuming you want to schedule the event 15 minutes before the specified time
    alert_time = event_date - timedelta(minutes=15)

    # Example: Send the event to the SQLite database
    send_to_database(event_name, event_time)

    print(f"Event scheduled: {event_name} at {event_time} on {event_month}")

    return alert_time

def alert_user(event_name, event_time):
    # Placeholder for alert logic
    print(f"Event alert: {event_name} at {event_time}")
    engine.say(f"Event alert: {event_name} at {event_time}")
    engine.runAndWait()

def get_response(user_input):
    messages.append({"role": "user", "content": user_input})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    ChatGPT_reply = response["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": ChatGPT_reply})
    return ChatGPT_reply

def recognize_and_respond():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        recognizer.dynamic_energy_threshold = 3000

        while True:
            try:
                print("Listening... ")
                audio = recognizer.listen(source, timeout=5.0)
                spoken_text = recognizer.recognize_google(audio)
                print(spoken_text)

                if "jarvis" in spoken_text.lower():
                    print(f"Recognized text: {spoken_text}")

                    if "can you hear me" in spoken_text.lower():
                        engine.say("Yes, I can hear you.")
                        engine.runAndWait()
                    else:
                        response_from_openai = get_response(spoken_text)

                        # Extract event details from spoken text
                        event_name, event_time, event_month = parse_spoken_text(response_from_openai)

                        if event_name and event_time and event_month:
                            schedule_event(event_name, event_time, event_month)
                        else:
                            print("Failed to parse event details.")

                # Check for scheduled events
                event_details = check_scheduled_events()

            except sr.UnknownValueError:
                print("Didn't recognize anything.")
            except sr.RequestError as e:
                print(f"Error with the Google Speech Recognition service: {e}")

def check_scheduled_events():
    try:
        # Retrieve the latest event from the SQLite database
        sqlite_cursor.execute('SELECT * FROM events ORDER BY ROWID DESC LIMIT 1')
        row = sqlite_cursor.fetchone()

        if row:
            event_name, event_time = row
            alert_user(event_name, event_time)
            print(f"Scheduled event arrived: {event_name} at {event_time}")

        # Optionally, you can return the event details
        return event_name, event_time if row else None
    except Exception as e:
        print(f"Error checking scheduled events from SQLite database: {e}")

# Example usage
recognize_and_respond()

# Close SQLite database connection when done
sqlite_connection.close()

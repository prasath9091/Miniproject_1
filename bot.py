import requests
from datetime import datetime, timedelta
import speech_recognition as sr
import pyttsx3
import sqlite3
import os
import dateutil.parser
from googletrans import Translator

# Initialize pyttsx3
engine = pyttsx3.init()
engine.setProperty('rate', 150)
news_api_key = "9418fb20ee6f46ff8fa490b718adec"
merriam_webster_api_key = "b43367a0-479c-452b-a323-c568ed302b"

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
        event_day TEXT,
        event_month TEXT,
        event_date TEXT
    )
''')
conn.commit()

current_year = datetime.now().year

def extract_time_day_and_month(text):
    try:
        parsed_date = dateutil.parser.parse(text, fuzzy=True)
        if "tomorrow" in text.lower():
            parsed_date += timedelta(days=1)
        return (
            parsed_date.strftime("%I:%M %p"),
            parsed_date.strftime("%A"),  # Extract day
            parsed_date.strftime("%B"),
            parsed_date.strftime("%d")  # Extract date
        )
    except ValueError:
        print("Error parsing date and time.")
        return None, None, None, None

def parse_spoken_text(spoken_text):
    # Initialize event_name to None
    event_name = None

    # Extract time, day, month, and date using the helper function extract_time_day_and_month
    event_time, event_day, event_month, event_date = extract_time_day_and_month(spoken_text)

    # Check if the spoken text includes "remind me to" or "schedule a"
    if "remind me to" in spoken_text.lower():
        event_name_split = spoken_text.lower().split("remind me to")
        if len(event_name_split) > 1:
            event_name = event_name_split[1].strip()

    elif "schedule a" in spoken_text.lower():
        event_name_split = spoken_text.lower().split("schedule a")
        if len(event_name_split) > 1:
            event_name = event_name_split[1].strip()

    # If no specific event name is extracted, use a default one ("default_event_name")
    if not event_name:
        event_name = "default_event_name"

    # Return the extracted information
    return event_name, event_time, event_day, event_month, event_date

def get_news(api_key, country_code='in'):
    try:
        url = f'https://newsapi.org/v2/top-headlines?country={country_code}&apiKey={api_key}'
        response = requests.get(url)
        news_data = response.json()
        
        # Extract headlines
        headlines = [article['title'] for article in news_data['articles']]
        
        # Print headlines in the terminal
        for idx, headline in enumerate(headlines, start=1):
            print(f"{idx}. {headline}")

        return headlines
    except Exception as e:
        print(f"Error fetching news: {e}")
        return None

def get_date_from_user():
    while True:
        user_input = input("When would you like to be reminded? ")
        try:
            parsed_date = dateutil.parser.parse(user_input, fuzzy=True)
            return (
                parsed_date.strftime("%I:%M %p"),
                parsed_date.strftime("%A"),  # Extract day
                parsed_date.strftime("%B"),
                parsed_date.strftime("%d")  # Extract date
            )
        except ValueError:
            print("Invalid date. Please provide a valid date like 'tomorrow', '20th January', or 'February 1st'.")


def get_time_from_user():
    while True:
        user_input = input("What time would you like to be reminded? ")
        try:
            parsed_time = dateutil.parser.parse(user_input, fuzzy=True)
            return parsed_time.strftime("%I:%M %p")
        except ValueError:
            print("Invalid time. Please provide a valid time in the format '2:00 PM'.")


def store_event_in_database(event_name, event_time, event_day, event_month, event_date):
    cursor.execute("INSERT INTO events (event_name, event_time, event_day, event_month, event_date) VALUES (?, ?, ?, ?, ?)",
                   (event_name, event_time, event_day, event_month, event_date))
    conn.commit()

    print(f"Event '{event_name}' successfully stored in the database.")

# ...

def schedule_event(event_name, event_time, event_day, event_month, event_date):
    # Check if day and month are provided
    if event_day and event_month:
        event_datetime_str = f"{event_month} {event_date} {current_year} {event_time}"
    else:
        print("Error: Both day and month must be provided for the event.")
        return None

    try:
        # Use dateutil.parser.parse for flexible parsing
        event_datetime = dateutil.parser.parse(event_datetime_str, fuzzy=True)

        # Check if AM or PM is specified in the event_time
        if "am" in event_time.lower() or "pm" in event_time.lower():
            event_datetime_str = event_datetime.strftime("%I:%M %p")  # Use the parsed AM/PM information
        else:
            print("Error: Please specify AM or PM in the event time.")
            return None

    except ValueError:
        print(f"Failed to parse event details: {event_name} at {event_time} on {event_day}, {event_month}")
        return None

    alert_time = event_datetime - timedelta(minutes=15)

    store_event_in_database(event_name, event_datetime_str, event_day, event_month, event_date)  # Store event in the database

    print(f"Event scheduled: {event_name} at {event_datetime_str} on {event_day}, {event_month}, {event_date}")

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
            event_name, event_time, event_day, event_month, event_date = row[1], row[2], row[3], row[4], row[5]

            # Print intermediate values for debugging
            print(f"Event Details: {event_name}, {event_time}, {event_day}, {event_month}, {event_date}")

            # Format the date consistently
            event_datetime_str = f"{event_month} {event_date} {current_year} {event_time}"

            print(f"Event Datetime String: {event_datetime_str}")

            try:
                # Use dateutil.parser.parse for flexible parsing
                event_datetime = dateutil.parser.parse(event_datetime_str, fuzzy=True)
            except ValueError:
                print(f"Failed to parse event_datetime_str: {event_datetime_str}")
                return None

            now = datetime.now()

            # Set the alert time 15 minutes before the scheduled event
            alert_time = event_datetime - timedelta(minutes=15)

            if now >= alert_time and now <= event_datetime:
                alert_user(event_name, event_time)
                print(f"Alert: Scheduled event '{event_name}' at {event_time} is approaching.")

            if now >= event_datetime:
                print(f"Scheduled event arrived: {event_name} at {event_time}")

                # Convert 24-hour format to 12-hour format with AM/PM
                formatted_time = event_datetime.strftime("%I:%M %p")
                print(f"The event is scheduled for {formatted_time}")

            return event_name, event_datetime.strftime("%I:%M %p")  # Format the time correctly

    except Exception as e:
        print(f"Error checking scheduled events: {e}")



def get_news_headlines(country='in', category='general', language='en', page_size=5):
    url = f'https://newsapi.org/v2/top-headlines'
    params = {
        'apiKey':'9418fb20ee6f46ff8fa490b718adece2',
        'country': country,
        'category': category,
        'language': language,
        'pageSize': page_size
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        return data.get('articles', [])
    else:
        print(f"Failed to fetch news headlines. Status code: {response.status_code}")
        return []

# new change
def get_word_meaning(word, api_key):
    url = f"https://www.dictionaryapi.com/api/v3/references/learners/json/{word}?key={api_key}"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                if data:
                    meaning = data[0].get('shortdef', ['Meaning not found'])[0]
                    return meaning
                else:
                    return "Meaning not found"
            else:
                return "Meaning not found"
        else:
            return "Meaning not found"

    except Exception as e:
        print(f"Error fetching meaning for '{word}': {e}")
        return "Meaning not found"


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
                    elif any(keyword in spoken_text.lower() for keyword in ["today's news", "what's in the news", "news today"]):
                        # Fetch and print today's news headlines
                        headlines = get_news_headlines()
                        if headlines:
                            print("\nToday's News Headlines:")
                            for idx, article in enumerate(headlines, start=1):
                                title = article.get('title', 'N/A')
                                print(f"{idx}. {title}")
                            print("\n")
                            engine.say("Here are today's top news headlines.")
                            engine.runAndWait()
                        else:
                            engine.say("Sorry, I couldn't fetch the news headlines.")
                            engine.runAndWait()
                    elif "define" in spoken_text.lower():
                        words = spoken_text.lower().split("define")
                        if len(words) > 1:
                            word_to_define = words[1].strip()
                            meaning = get_word_meaning(word_to_define, merriam_webster_api_key)
                            if meaning:
                                print(f"The meaning of '{word_to_define}' is: {meaning}")
                                engine.say(f"The meaning of '{word_to_define}' is: {meaning}")
                                engine.runAndWait()
                            else:
                                print(f"Failed to fetch meaning for '{word_to_define}'.")
                                engine.say(f"Failed to fetch meaning for '{word_to_define}'.")
                                engine.runAndWait()
                        else:
                            print("No word specified for definition.")
                            engine.say("No word specified for definition.")
                            engine.runAndWait()
                    else:
                        event_name, event_time, event_day, event_month, event_date = parse_spoken_text(spoken_text)

                        if event_name and event_time and event_month and event_date:
                            response = f"Scheduled: {event_name} at {event_time} on {event_day}, {event_month}, {event_date}"
                            engine.say(response)
                            engine.runAndWait()

                            alert_time = schedule_event(event_name, event_time, event_day, event_month, event_date)

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
    try:
        recognize_and_respond()
    except KeyboardInterrupt:
        print("\nExiting the program.")
        conn.close()

import requests
from datetime import datetime, timedelta
import pyttsx3
import speech_recognition as sr
import openai

# Initialize pyttsx3
engine = pyttsx3.init()

# Set your openai api key and customize the chatgpt role
openai.api_key = "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"
messages = [{"role": "system", "content": "Your name is Jarvis and give answers in 2 lines"}]

# ThingSpeak API credentials
thing_speak_api_key = "6BWUBK9COKV7TFUR"
channel_id = 2336541
read_api_key = "NMX0T8FDOCOA3BX1"

def send_to_thingspeak(event_name, event_time):
    # Replace this with your actual ThingSpeak logic
    api_url = f"https://api.thingspeak.com/update?api_key={thing_speak_api_key}&field1={event_name}&field2={event_time}"

    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            print(f"Event '{event_name}' sent to ThingSpeak successfully.")
        else:
            print(f"Error sending event '{event_name}' to ThingSpeak. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending event '{event_name}' to ThingSpeak: {e}")

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

    # Example: Send the event to ThingSpeak
    send_to_thingspeak(event_name, event_time)

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

# Example usage
recognize_and_respond()
def check_scheduled_events():
    try:
        # Replace this with your ThingSpeak API logic to retrieve events
        api_url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json?api_key={read_api_key}&results=1"
        response = requests.get(api_url)
        data = response.json()

        if 'feeds' in data and len(data['feeds']) > 0:
            # Extract event details from the retrieved data
            event_name = data['feeds'][0]['field1']
            event_time = data['feeds'][0]['field2']

            # Convert event_time to datetime object for comparison
            event_datetime = datetime.strptime(event_time, "%Y-%m-%dT%H:%M:%SZ")

            # Compare with the current time
            now = datetime.now()
            if now >= event_datetime:
                alert_user(event_name, event_time)
                print(f"Scheduled event arrived: {event_name} at {event_time}")

            # Optionally, you can return the event details
            return event_name, event_time
    
    except Exception as e:
        print(f"Error checking scheduled events: {e}")

# Call this function within your main loop



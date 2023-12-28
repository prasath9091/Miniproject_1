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
thing_speak_api_key = "your_thingspeak_api_key"
channel_id = "your_channel_id"

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

def recognize_and_schedule():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening...")
        audio = recognizer.listen(source, timeout = 5.0)

        try:
            spoken_text = recognizer.recognize_google(audio)
            print(f"Recognized text: {spoken_text}")

            if "jarvis" in spoken_text.lower():
                if "can you hear me" in spoken_text.lower():
                    engine.say("Yes, I can hear you.")
                    engine.runAndWait()

                response_from_openai = get_response(spoken_text)

                # Extract event details from spoken text
                event_name, event_time, event_month = parse_spoken_text(response_from_openai)

                if event_name and event_time and event_month:
                    alert_time = schedule_event(event_name, event_time, event_month)

                    # Capture the current system time
                    now = datetime.now()

                    # Check if it's time to alert
                    if now >= alert_time:
                        alert_user(event_name, event_time)
                    else:
                        print(f"Event scheduled: {event_name} at {event_time} on {event_month}")
                else:
                    print("Failed to parse event details.")

        except sr.UnknownValueError:
            print("Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")

# Example usage
recognize_and_schedule()

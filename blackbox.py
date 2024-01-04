import speech_recognition as sr
import pyttsx3
import datetime
import requests
import time

class VoiceAssistant:
    def __init__(self, api_key, channel_id, wake_word="jarvis"):
        self.r = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.wake_word = wake_word
        self.api_key = api_key
        self.channel_id = channel_id
        self.listening = False

    def listen(self):
        with sr.Microphone() as source:
            print("Listening...")
            audio = self.r.listen(source)
            try:
                text = self.r.recognize_google(audio)
                print("You said: " + text)
                if text.lower() == self.wake_word:
                    self.listening = True
            except sr.UnknownValueError:
                print("Sorry, I did not get that")

    def send_data(self, event, date, time):
        data = {"field1": event, "field2": date, "field3": time}
        url = f"https://api.thingspeak.com/update?api_key={self.api_key}&channel={self.channel_id}"
        try:
            requests.post(url, data=data)
        except requests.RequestException as e:
            print(f"Error sending data: {e}")

    def get_data(self):
        url = f"https://api.thingspeak.com/channels/{self.channel_id}/fields/last.json?api_key={self.api_key}"
        try:
            response = requests.get(url)
            data = response.json()
            return data["feeds"][0]["field1"], data["feeds"][0]["field2"], data["feeds"][0]["field3"]
        except requests.RequestException as e:
            print(f"Error getting data: {e}")
            return None, None, None

    def process_user_input(self, user_input):
        event, date, time = user_input.split(" ")
        self.send_data(event, date, time)

        while True:
            current_time = datetime.datetime.now().strftime("%H %M")
            if current_time == time:
                event, date, time = self.get_data()
                tts_text = f"The event {event} on {date} at {time} has been recorded"
                self.engine.say(tts_text)
                self.engine.runAndWait()
                break
            time.sleep(1)

    def main_loop(self):
        while True:
            if self.listening:
                self.listen()
                text = self.r.recognize_google(self.r.listen())
                self.process_user_input(text)
                self.listening = False
            else:
                self.listen()

if __name__ == "__main__":
    # Replace with your API key and channel ID
    api_key = "YOUR_API_KEY"
    channel_id = "YOUR_CHANNEL_ID"
    
    assistant = VoiceAssistant(api_key, channel_id)
    assistant.main_loop()

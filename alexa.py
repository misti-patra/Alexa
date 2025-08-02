wake_word_detected = False

import speech_recognition as sr
import pyttsx3
import pywhatkit
import datetime
import wikipedia
import pyjokes
import requests  # for weather
import os
import time
import smtplib
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import difflib
import cv2

with open("log.txt", "a") as f:
    f.write("=== New Alexa Session Started ===\n")

listener = sr.Recognizer()
engine = pyttsx3.init()

# Voice config
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)

# Chat logging
def log_interaction(user_input, alexa_response):
    with open("log.txt", "a", encoding="utf-8") as file:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{now}] User: {user_input}\n")
        file.write(f"[{now}] Alexa: {alexa_response}\n\n")

def talk(text):
    print("Alexa:", text)
    engine.say(text)
    engine.runAndWait()
    log_interaction("TBD", text)

# Weather using OpenWeatherMap API
def get_weather(city):
    api_key = 'Create Your own API key'  # Replace with your API key
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
    try:
        response = requests.get(url).json()
        if response.get("cod") != 200:
            return "I couldn't get the weather right now."
        temp = response['main']['temp']
        description = response['weather'][0]['description']
        return f"The temperature in {city} is {temp}°C with {description}."
    except:
        return "Weather service is unavailable."

def open_application(app_name):
    if 'chrome' in app_name:
        os.system("start chrome")
    elif 'notepad' in app_name:
        os.system("start notepad")
    elif 'calculator' in app_name:
        os.system("start calc")
    else:
        talk("I can't open that app.")

def set_alarm(hour, minute):
    talk(f"Alarm set for {hour}:{minute}")
    while True:
        now = datetime.datetime.now()
        if now.hour == hour and now.minute == minute:
            talk("Wake up! This is your alarm.")
            break
        time.sleep(10)

def send_email(receiver, subject, body):
    sender_email = "your_email@gmail.com"
    sender_password = "your_app_password"
    email_text = f"Subject: {subject}\n\n{body}"
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver, email_text)
        server.quit()
        talk("Email has been sent.")
    except Exception as e:
        print("Error:", e)
        talk("Sorry, I was unable to send the email.")

# Vosk Model
model = Model(r"C:\Documents\MISTI\Python first project\vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(model, 16000)

def callback(indata, frames, time_info, status):
    global wake_word_detected
    if status:
        print(status)
    data_bytes = indata.tobytes()
    if recognizer.AcceptWaveform(data_bytes):
        result = json.loads(recognizer.Result())
        text = result.get("text", "").lower()
        print("Vosk heard:", text)
        if "alexa" in text:
            print("Wake word detected! Listening for command...")
            wake_word_detected = True

def run_alexa(command):
    if not command:
        return

    if 'stop' in command or 'exit' in command or 'bye' in command:
        response = "Goodbye! Have a great day."
        talk(response)
        log_interaction(command, response)
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write("=== Alexa Session Ended ===\n\n")
        exit()

    elif 'play' in command:
        song = command.replace('play', '')
        response = 'Playing ' + song
        talk(response)
        pywhatkit.playonyt(song)
        log_interaction(command, response)

    elif 'time' in command:
        time_now = datetime.datetime.now().strftime('%I:%M %p')
        response = 'Current time is ' + time_now
        talk(response)
        log_interaction(command, response)

    elif 'who the heck is' in command:
        try:
            person = command.replace('who the heck is', '')
            info = wikipedia.summary(person, 1)
            talk(info)
            log_interaction(command, info)
        except:
            response = "I couldn't find information on that."
            talk(response)
            log_interaction(command, response)

    elif 'date' in command:
        response = 'Sorry, I have a headache.'
        talk(response)
        log_interaction(command, response)

    elif 'are you single' in command:
        response = 'I am in a relationship with Wi-Fi.'
        talk(response)
        log_interaction(command, response)

    elif 'joke' in command:
        joke = pyjokes.get_joke()
        talk(joke)
        log_interaction(command, joke)

    elif 'weather' in command:
        retries = 3
        for attempt in range(retries):
            talk("Which city?")
            with sr.Microphone() as source:
                listener = sr.Recognizer()
                listener.energy_threshold = 300
                listener.pause_threshold = 0.8
                try:
                    city_audio = listener.listen(source, timeout=8)
                    city = listener.recognize_google(city_audio).lower()
                    print("Recognized city:", city)
                    weather_info = get_weather(city)
                    talk(weather_info)
                    log_interaction(command + " " + city, weather_info)
                    break
                except Exception as e:
                    print("City recognition failed:", e)
                    if attempt < retries - 1:
                        talk("I didn't catch that. Please say the city name again.")
                    else:
                        talk("I couldn't get the weather right now.")
                        log_interaction(command, "City name not recognized after retries.")

    elif 'open' in command:
        app = command.replace('open', '').strip()
        open_application(app)
        log_interaction(command, f"Tried opening {app}")

    elif 'set alarm' in command:
        talk("Tell me the time in HH:MM format.")
        with sr.Microphone() as source:
            listener = sr.Recognizer()
            try:
                time_audio = listener.listen(source, timeout=5)
                alarm_time = listener.recognize_google(time_audio).strip()
                hour, minute = map(int, alarm_time.split(':'))
                set_alarm(hour, minute)
                log_interaction(command, f"Alarm set for {alarm_time}")
            except:
                talk("Invalid time format.")
                log_interaction(command, "Alarm time invalid")

    elif 'send email' in command:
        talk("What is the receiver's email?")
        with sr.Microphone() as source:
            listener = sr.Recognizer()
            try:
                recv_audio = listener.listen(source, timeout=5)
                receiver = listener.recognize_google(recv_audio).replace(' ', '').lower()
                talk("What is the subject?")
                subject_audio = listener.listen(source, timeout=5)
                subject = listener.recognize_google(subject_audio)
                talk("What is the message?")
                body_audio = listener.listen(source, timeout=5)
                body = listener.recognize_google(body_audio)
                send_email(receiver, subject, body)
                log_interaction(command, f"Email sent to {receiver}")
            except:
                talk("Email sending failed.")
                log_interaction(command, "Email failed")

    elif 'click photo' in command or 'take photo' in command:
        try:
            cam = cv2.VideoCapture(0)
            ret, frame = cam.read()
            if ret:
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'photo_{timestamp}.png'
                cv2.imwrite(filename, frame)
                response = f"Photo clicked and saved as {filename}"
            else:
                response = "Failed to access the camera."
            cam.release()
            talk(response)
            log_interaction(command, response)
        except Exception as e:
            print("Camera error:", e)
            talk("I couldn't click the photo.")
            log_interaction(command, "Camera error")
    
    else:
        response = 'Please say the command again.'
        talk(response)
        log_interaction(command, response)

def listen_vosk():
    global wake_word_detected
    while True:
        wake_word_detected = False
        print("Listening for 'Alexa' wake word...")
        stream = sd.InputStream(samplerate=16000, blocksize=8000, dtype='int16',
                                channels=1, callback=callback)
        with stream:
            while not wake_word_detected:
                time.sleep(0.1)

        talk("Yes?")
        with sr.Microphone() as source:
            listener = sr.Recognizer()
            try:
                print("Listening for command...")
                audio = listener.listen(source, timeout=5)
                command_text = listener.recognize_google(audio).lower()
                print("User:", command_text)
                run_alexa(command_text)
            except Exception as e:
                print("Didn't catch that:", e)

# Start assistant

listen_vosk()


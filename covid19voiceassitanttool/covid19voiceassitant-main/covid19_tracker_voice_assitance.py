#Importing all libraries
import requests
import json
import pyttsx3
import speech_recognition as speech_recognition
import re
import threading
import time


API_KEY="YOUR_API_KEY"
PROJECT_TOKEN="YOUR_PROJECT_TOKEN"
RUN_TOKEN="YOUR_RUN_TOKEN"

response = requests.get(f'https://parsehub.com/api/v2/projects/{PROJECT_TOKEN}/last_ready_run/data', params={"api_key": API_KEY})
data = json.loads(response.text)

class Data:
    def __init__(self, api_key, project_token):
        self.api_key = api_key
        self.project_token=project_token
        self.params={
            "api_key":self.api_key
        }
        self.data = self.get_data()

    def get_data(self):
        response = requests.get(f'https://parsehub.com/api/v2/projects/{PROJECT_TOKEN}/last_ready_run/data', params={"api_key": API_KEY})
        self.data = json.loads(response.text)
        return data

    def get_total_cases(self):
        data =  self.data['Totals']
        for content in data:
            if content ['name'] == "Coronavirus Cases:": 
                return content['Values']
   
    def get_total_deaths(self):
        data =  self.data['Totals']
        for content in data:
            if content ['name'] == "Deaths:":
                return content['Values']

    def get_country_data(self, country):
        data = self.data['country']
        for content in data:
            if content ['name'].lower() == country.lower():
                return content
        return "0"
    
    def get_list_of_countries(self):
        countries = []
        for country in self.data['country']:
            countries.append(country['name'].lower())
        return countries
    
    def update_data(self):
        response = requests.post(f'https://parsehub.com/api/v2/projects/{self.project_token}/run', params=self.params)
        def poll(): 
            time.sleep(0.1)
            old_data = self.data
            while True:
                new_data = self.get_data()
                if new_data != old_data:
                    self.data = new_data
                    print("data has been updated")
                    break
                time.sleep(5)
        t = threading.Thread(target=poll)
        t.start()

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def get_audio():
    r = speech_recognition.Recognizer()
    with speech_recognition.Microphone() as source:
        audio = r.listen(source)
        said= ""

        try:
            said= r.recognize_google(audio)
        except Exception as e:
            print("Exception:", str(e))
    
    return said.lower()

def main():
    print("Started the program!")
    data = Data(API_KEY, PROJECT_TOKEN)
    END_PHRASE = "exit"
    country_list = data.get_list_of_countries()
    TOTAL_PATTERNS = { 
                    re.compile("[\w\s]+ total + [\w\s] + cases"):data.get_total_cases,
                    re.compile("[\w\s]+ total cases"): data.get_total_cases,
                    re.compile("[\w\s]+ total [\w\s] + deaths"):data.get_total_deaths,
                    re.compile("[\w\s]+ total deaths"):data.get_total_deaths
                    }
    COUNTRY_PATTERNS={re.compile("[\w\s]+ cases [\w\s]+"): lambda country: data.get_country_data(country)['total_cases'], 
    re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.get_country_data(country)['total_deaths'],}
    
    UPDATE_COMMAND = "update"
    while True:
        print("Listening to you....")
        text= get_audio()
        print (text)
        result = None   

        for pattern, func in COUNTRY_PATTERNS.items():
            if pattern.match(text):
                words = set(text.split(" "))
                for country in country_list:
                    if country in words:      
                        result =func(country)
                        break 
        
        for pattern, func in TOTAL_PATTERNS.items():
            if pattern.match(text):
                result= func()
                break 
        
        if text == UPDATE_COMMAND:
            result = "Data is being updated. Please wait."
            data.update_data()
            
        if result:
            print(result)
            speak(result)
            
        if text.find(END_PHRASE) !=-1:
            break
main()

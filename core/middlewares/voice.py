import speech_recognition as sr
import os

# get the current working directory
cwd = os.getcwd()

recognizer = sr.Recognizer()

def get_text_from_audio(filename):
    result = ""
    filepath = f"{cwd}/core/data/voice/wav/{filename}.wav"
    audio_file = sr.AudioFile(filepath)
    
    try:
        with audio_file as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.record(source)
            result = recognizer.recognize_google(audio, language='ru')

    except:
        result = False    

    return result
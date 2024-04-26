
> This project is the progression from an older project: https://github.com/dom1111111/super_notes_app_2

# Description

This is a framework written in Python to build an extensible, general purpose personal assistant and/or a customizable computer interface.

Central to its operation is a collection of commands which specify context and input requirements, and a corresponding action should the requirements be met. These are written in JSON format, using a simple syntax to describe requirement and action behavior. Actions can be created from referencing existing internal functions or by providing a map of strings to other functions of your choice.

Some noteworthy features are:
- a multitude of options for command input. In particular a robust, offline, and *fast* voice input system
- a simple JSON-based syntax for creating commands and fast internal command parser
- a simple Tkinter GUI for visual interaction
- a few sub-apps which can be used to provide functionality to commands

# Setup and Usage

An example of written commands, and setting up and running the app can be found in `example_1_com_data.json` and `example_1.py`.

## Dependencies needed
- Pyttsx4 - https://github.com/Jiangshan00001/pyttsx4 - for text-to-speech
- Numpy - https://github.com/numpy/numpy
- Vosk - https://github.com/alphacep/vosk-api - for speech recognition
    - using small model: https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
        - must extract the zip and place the `vosk-model-small-en-us-0.15` folder in `app/GUI_audio_voice/vosk_models`
- Faster Whisper (OpenAI Whisper) - https://github.com/guillaumekln/faster-whisper - for speech recognition
    - using the `tiny.en` model
- PyAudio - https://people.csail.mit.edu/hubert/pyaudio/ - for playing and recording audio
- PyAutoGUI - https://github.com/asweigart/pyautogui - for keyboard and mouse input detection and control

from utils.speechtotext import speech_to_text

if __name__ == "__main__":
    try:
        text = speech_to_text()
        if text is not None:
            print(text)
    except Exception as ex:
        print(str(ex))

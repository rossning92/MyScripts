import pytesseract
from PIL import ImageGrab
import os
import sys
import shutil

def setup_tesseract():
    if shutil.which(pytesseract.pytesseract.tesseract_cmd):
        return True

    if sys.platform == "win32":
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Users\%USERNAME%\AppData\Local\Tesseract-OCR\tesseract.exe",
        ]
        for path in common_paths:
            full_path = os.path.expandvars(path)
            if os.path.exists(full_path):
                pytesseract.pytesseract.tesseract_cmd = full_path
                return True
    return False

def get_screen_text():
    screenshot = ImageGrab.grab()
    
    text = pytesseract.image_to_string(screenshot)
    
    return text.strip()

if __name__ == "__main__":
    if not setup_tesseract():
        print("Tesseract not found. Please install it or add it to your PATH.")
        exit(1)
        
    print("Capturing screen and extracting text...")
    text = get_screen_text()
    
    if text:
        print("-" * 20)
        print(text)
        print("-" * 20)
    else:
        print("No text detected.")


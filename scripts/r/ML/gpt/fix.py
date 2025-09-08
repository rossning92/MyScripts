import sys

from ML.gpt.chat_menu import complete_chat_gui

complete_chat_gui(
    prompt_text="Fix the spelling and grammar of the following text and only return the corrected text",
    input_text=sys.argv[1],
    model="gpt-3.5-turbo",
)

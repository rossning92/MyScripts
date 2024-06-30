import sys

from ML.gpt.chatmenu import complete_chat

complete_chat(
    prompt_text="Fix the spelling and grammar of the following text and only return the corrected text",
    input_text=sys.argv[1],
    model="gpt-3.5-turbo",
)

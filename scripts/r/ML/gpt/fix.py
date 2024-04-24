import sys

from ML.gpt.chatgpt import complete_chat

complete_chat(
    prompt_text="Fix the spelling and grammar of the following text and only return the corrected text",
    input_text=sys.argv[1],
)

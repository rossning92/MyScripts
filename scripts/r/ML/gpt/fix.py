import sys

from ML.gpt.chatgpt2 import complete_chat

prompt = "Fix the spelling and grammar of the following text and only return the corrected text:"
complete_chat(copy_to_clipboard=True, prompt_text=prompt, input=sys.argv[1])

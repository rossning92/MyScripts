import sys

from ML.gpt.chatgpt2 import complete_chat

prompt = "For optimising the grammar, clarity and conciseness of text and improving readability.\n\nAs a writing improvement assistant, your task is to improve the spelling, grammar, clarity, concision, and overall readability of the text provided, while breaking down long sentences, reducing repetition, and providing suggestions for improvement, in everyday language. Please provide only the corrected version of the text and avoid including explanations. Please begin by editing the following text:"
complete_chat(copy_to_clipboard=True, prompt_text=prompt, input=sys.argv[1])

import sys

from ML.gpt.chat_menu import complete_chat_gui

complete_chat_gui(
    prompt_text=(
        "For optimising the grammar, clarity and conciseness of text and improving readability. "
        "As a writing improvement assistant, your task is to improve the spelling, grammar, clarity, concision, and overall readability of the text provided, while breaking down long sentences, reducing repetition, and providing suggestions for improvement, in everyday language. "
        "Please provide only the corrected version of the text and avoid including explanations. "
        "Please begin by editing the following text"
    ),
    input_text=sys.argv[1],
)

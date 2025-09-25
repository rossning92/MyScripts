import sys
from pathlib import Path

from ML.gpt.chat_menu import ChatMenu

input_text = Path(sys.argv[-1]).read_text(encoding="utf-8")
ChatMenu(
    message=(
        "Fix the spelling and grammar of the following text and only return the corrected text:\n"
        "-------\n"
        f"{input_text}\n"
        "-------"
    ),
    model="gpt-4o-mini",
    copy_and_exit=True,
).exec()

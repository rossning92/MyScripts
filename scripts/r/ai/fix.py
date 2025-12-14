import sys
from pathlib import Path

from ai.chat_menu import ChatMenu

input_text = Path(sys.argv[-1]).read_text(encoding="utf-8")
ChatMenu(
    message=(
        "Fix the spelling and grammar of the following text and only return the corrected text:\n"
        "-------\n"
        f"{input_text}\n"
        "-------"
    ),
    # model="gpt-3.5-turbo",
    model="gpt-4o-mini",
    copy=True,
).exec()

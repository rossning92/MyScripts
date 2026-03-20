from tts import tts as _tts
from utils.menu.asynctaskmenu import AsyncTaskMenu


def tts(text: str):
    """
    Convert text to speech and play it.
    """
    menu = AsyncTaskMenu(
        target=lambda stop_event: _tts(text, stop_event=stop_event),
        prompt="Playing TTS",
        prompt_color="green",
        items=text.splitlines(),
        wrap_text=True,
    )
    menu.exec()

import argparse
import json
import os
import signal
import subprocess
import time
import urllib.error
import urllib.request
from threading import Event
from typing import Optional


def tts(
    text: str,
    out_file: Optional[str] = None,
    stop_event: Optional[Event] = None,
    voice: str = "shimmer",  # Test results showed 'shimmer' is often faster
):
    # For real-time playback, 'pcm' or 'wav' are fast.
    is_realtime = out_file is None
    fmt = "pcm" if is_realtime else (os.path.splitext(out_file)[1].lstrip(".") or "mp3")

    data = json.dumps(
        {
            "model": "tts-1",
            "input": text,
            "voice": voice,
            "response_format": fmt,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=data,
        headers={
            "Authorization": f'Bearer {os.environ["OPENAI_API_KEY"]}',
            "Content-Type": "application/json",
        },
        method="POST",
    )

    process = None
    if is_realtime:
        # Start the player process immediately to reduce startup latency
        # 24kHz, 16-bit signed-integer, mono, little-endian.
        process = subprocess.Popen(
            [
                "play",
                "--volume",
                "4",
                "-q",
                "--buffer",
                "1024",
                "-t",
                "raw",
                "-r",
                "24k",
                "-e",
                "signed-integer",
                "-b",
                "16",
                "-c",
                "1",
                "-",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            bufsize=0,
        )

    try:
        with urllib.request.urlopen(req) as response:
            if not is_realtime:
                # Saving to file - simple implementation
                with open(out_file, "wb") as f:
                    while True:
                        chunk = response.read(4096)
                        if not chunk:
                            break
                        f.write(chunk)
            else:
                # Real-time playback
                try:
                    while True:
                        chunk = response.read(4096)
                        if not chunk:
                            break

                        if stop_event and stop_event.is_set():
                            process.send_signal(signal.SIGINT)
                            break

                        if process.stdin and chunk:
                            try:
                                process.stdin.write(chunk)
                                process.stdin.flush()
                            except BrokenPipeError:
                                break
                finally:
                    if process.stdin:
                        process.stdin.close()

                    # Wait for process to finish
                    while process.poll() is None:
                        if stop_event and stop_event.is_set():
                            process.send_signal(signal.SIGINT)
                            break
                        time.sleep(0.01)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        raise Exception(f"OpenAI API Error {e.code}: {error_body}")
    finally:
        if process and process.poll() is None:
            process.terminate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "text",
        type=str,
        nargs="?",
        default="Today is a wonderful day to build something people love!",
        help="Text to be converted to speech",
    )
    parser.add_argument(
        "-o",
        "--out_file",
        type=str,
        help="Output file to save the speech audio (default: play directly)",
    )
    parser.add_argument(
        "-v",
        "--voice",
        type=str,
        default="shimmer",
        help="Voice to use (default: shimmer)",
    )
    args = parser.parse_args()

    tts(args.text, out_file=args.out_file, voice=args.voice)

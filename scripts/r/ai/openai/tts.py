import argparse
import os
import signal
import subprocess
import time
from threading import Event
from typing import Optional

import httpx

# Use a global httpx Client for connection pooling and HTTP/2 support
_client = httpx.Client(http2=True)


def tts(
    text: str,
    out_file: Optional[str] = None,
    stop_event: Optional[Event] = None,
    voice: str = "shimmer",  # Test results showed 'shimmer' is often faster
):
    global _client

    # For real-time playback, 'pcm' or 'wav' are fast.
    is_realtime = out_file is None
    format = (
        "pcm" if is_realtime else (os.path.splitext(out_file)[1].lstrip(".") or "mp3")
    )

    if not is_realtime:
        # Saving to file - simple implementation
        with _client.stream(
            "POST",
            "https://api.openai.com/v1/audio/speech",
            headers={
                "Authorization": f'Bearer {os.environ["OPENAI_API_KEY"]}',
                "Content-Type": "application/json",
            },
            json={
                "model": "tts-1",
                "input": text,
                "voice": voice,
                "response_format": format,
            },
        ) as response:
            if response.status_code != 200:
                raise Exception(f"OpenAI API Error {response.status_code}: {response.text}")
            with open(out_file, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
    else:
        # Real-time playback
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
            start_time = time.time()
            first_chunk_received = False
            
            with _client.stream(
                "POST",
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f'Bearer {os.environ["OPENAI_API_KEY"]}',
                    "Content-Type": "application/json",
                },
                json={
                    "model": "tts-1",
                    "input": text,
                    "voice": voice,
                    "response_format": format,
                },
            ) as response:
                if response.status_code != 200:
                    raise Exception(f"OpenAI API Error {response.status_code}: {response.text}")
                
                for chunk in response.iter_bytes():
                    if not first_chunk_received:
                        # Log latency for testing
                        # print(f"Latency to first chunk: {time.time() - start_time:.3f}s")
                        first_chunk_received = True
                    
                    if stop_event and stop_event.is_set():
                        process.send_signal(signal.SIGINT)
                        break
                    
                    if process.stdin and chunk:
                        try:
                            process.stdin.write(chunk)
                            process.stdin.flush()
                        except BrokenPipeError:
                            break
            
            if process.stdin:
                process.stdin.close()
            
            # Wait for process to finish
            while process.poll() is None:
                if stop_event and stop_event.is_set():
                    process.send_signal(signal.SIGINT)
                    break
                time.sleep(0.01)
        finally:
            if process.poll() is None:
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

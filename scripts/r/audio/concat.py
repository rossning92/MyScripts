import argparse
import os

from utils.audio import concat_audio

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()

    silence_secs = float("{{_SILENCE_SECS}}") if "{{_SILENCE_SECS}}" else 1.0
    audio_files = [os.path.abspath(path) for path in args.files]
    base_dir = os.path.dirname(audio_files[0]) or "."
    os.chdir(base_dir)

    os.makedirs("tmp", exist_ok=True)
    concat_audio(audio_files, silence_secs, out_file=os.path.join("tmp", "concat.wav"))

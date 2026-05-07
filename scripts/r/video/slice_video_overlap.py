import subprocess
import os
import sys

def get_duration(filename):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    return float(result.stdout.strip())

def slice_video(input_file, segment_duration=21, overlap=1):
    try:
        duration = get_duration(input_file)
    except Exception as e:
        print(f"Error getting duration: {e}")
        return

    input_dir = os.path.dirname(os.path.abspath(input_file))
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    out_dir = os.path.join(input_dir, f"{base_name}_parts")
    os.makedirs(out_dir, exist_ok=True)

    step = segment_duration - overlap
    i = 0
    start = 0
    while True:
        output_file = os.path.join(out_dir, f"{i:03d}.mp4")
        
        print(f"Generating {output_file} (start={start}s, duration={segment_duration}s)...")
        cmd = [
            "ffmpeg", "-y",
            "-loglevel", "error",
            "-ss", str(start),
            "-i", input_file,
            "-t", str(segment_duration),
            "-r", "25",
            "-c:v", "libx264",
            "-crf", "23",
            "-c:a", "aac",
            output_file
        ]
        subprocess.run(cmd, check=True)
        
        if start + segment_duration >= duration:
            break
            
        start += step
        i += 1

if __name__ == "__main__":
    video_file = os.environ.get("INPUT_VIDEO")
    if not video_file:
        print("Error: INPUT_VIDEO environment variable is not set.")
        sys.exit(1)
    
    seg_time = int(os.environ.get("SEGMENT_TIME", 21))
    overlap_time = int(os.environ.get("OVERLAP_TIME", 1))
    
    slice_video(video_file, segment_duration=seg_time, overlap=overlap_time)

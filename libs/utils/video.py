import subprocess
from typing import Optional


class VideoWriter:
    def __init__(self, out_path: str | None = None, fps=60):
        self.fps = fps
        self.out_path = out_path
        self.video_proc: Optional[subprocess.Popen] = None

    def _start(self, frame):
        if self.out_path and frame is not None and self.video_proc is None:
            height, width = frame.shape[:2]
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "rawvideo",
                "-vcodec",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "-s",
                f"{width}x{height}",
                "-r",
                f"{self.fps}",
                "-i",
                "-",
                "-an",
                "-vcodec",
                "libx264",
                "-crf",
                "1",
                "-pix_fmt",
                "yuv420p",
                self.out_path,
            ]
            self.video_proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    def write(self, frame):
        if self.out_path and frame is not None:
            self._start(frame)
            if self.video_proc and self.video_proc.stdin:
                self.video_proc.stdin.write(frame.tobytes())

    def close(self):
        if self.video_proc and self.video_proc.stdin:
            self.video_proc.stdin.close()
        if self.video_proc:
            self.video_proc.wait()
            self.video_proc = None

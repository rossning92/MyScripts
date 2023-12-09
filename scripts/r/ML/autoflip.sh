docker run -it -v C:\tmp:/video -e input_video=input.mp4 -e output_video=output.mp4 -e aspect_ratio=9:16 -e config=development lathi/autoflip:latest

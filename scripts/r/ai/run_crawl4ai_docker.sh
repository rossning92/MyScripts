# https://github.com/unclecode/crawl4ai/tree/main?tab=readme-ov-file#for-amd64-regular-linuxwindows
docker pull unclecode/crawl4ai:latest
docker run -d -p 11235:11235 --name crawl4ai --shm-size=1g unclecode/crawl4ai:latest

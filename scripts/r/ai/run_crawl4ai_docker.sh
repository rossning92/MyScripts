# https://github.com/unclecode/crawl4ai/tree/main?tab=readme-ov-file#for-amd64-regular-linuxwindows
docker pull unclecode/crawl4ai:basic-amd64
docker run -d --name crawl4ai -e CRAWL4AI_API_TOKEN=your_secret_token -p 11235:11235 unclecode/crawl4ai:basic-amd64

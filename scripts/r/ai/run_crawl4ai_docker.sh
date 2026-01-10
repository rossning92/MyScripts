# https://github.com/unclecode/crawl4ai?tab=readme-ov-file#getting-started
docker pull unclecode/crawl4ai:latest
docker run -d -p 11235:11235 --name crawl4ai --shm-size=1g unclecode/crawl4ai:latest
# Visit the monitoring dashboard at http://localhost:11235/dashboard
# Or the playground at http://localhost:11235/playground

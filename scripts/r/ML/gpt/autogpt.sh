# https://docs.agpt.co/autogpt/setup/docker/

set -e

cd ~/Projects
mkdir -p AutoGPT
cd AutoGPT

cat >docker-compose.yml <<EOF
version: "3.9"
services:
  auto-gpt:
    image: significantgravitas/auto-gpt
    env_file:
      - .env
    ports:
      - "8000:8000"  # remove this if you just want to run a single agent in TTY mode
    profiles: ["exclude-from-up"]
    volumes:
      - ./data:/app/data
      ## allow auto-gpt to write logs to disk
      - ./logs:/app/logs
      ## uncomment following lines if you want to make use of these files
      ## you must have them existing in the same folder as this docker-compose.yml
EOF

curl -o .env https://raw.githubusercontent.com/Significant-Gravitas/AutoGPT/master/autogpt/.env.template
sed -i "s/# OPENAI_API_KEY=.*/OPENAI_API_KEY=\{{OPENAI_API_KEY}}/g" .env

docker pull significantgravitas/auto-gpt

docker compose run --rm auto-gpt

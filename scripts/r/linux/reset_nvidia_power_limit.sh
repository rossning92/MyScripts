#!/usr/bin/env bash
set -euo pipefail

gpu_index="${1:-0}"
default_limit="$(nvidia-smi -i "$gpu_index" --query-gpu=power.default_limit --format=csv,noheader,nounits)"

sudo nvidia-smi -i "$gpu_index" -pl "$default_limit"
sudo nvidia-settings -a "[gpu:$gpu_index]/GPUFanControlState=0"
echo "GPU $gpu_index power limit restored to ${default_limit} W"
echo "GPU $gpu_index fan control restored to automatic"

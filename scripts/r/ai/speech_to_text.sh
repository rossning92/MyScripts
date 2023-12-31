set -e

# Create a temp dir.
temp_dir=$(mktemp -d)
if [[ ! "$temp_dir" || ! -d "$temp_dir" ]]; then
    echo "Could not create temp dir"
    exit 1
fi

# Clean up the temp dir on exiting.
function cleanup {
    rm -rf "$temp_dir"
}
trap cleanup EXIT

cd "$temp_dir"

run_script r/audio/record_audio.sh recording.mp3

# Start recognition.
run_script r/ai/openai/audio_to_text.sh recording.mp3

set -o pipefail
echo "Converting audio to text: $1"
filename=$(basename "$1")
output="${filename%.*}_transcription.json"
curl --request POST \
	--url https://api.openai.com/v1/audio/transcriptions \
	--header "Authorization: Bearer $OPENAI_API_KEY" \
	--header 'Content-Type: multipart/form-data' \
	--form file=@"$1" \
	--form model=whisper-1 | tee "$output"

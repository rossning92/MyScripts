set -e

# Make a keystore file with keytool and check it
# keytool -genkey -v -keystore '{{KEYSTORE_FILE}}' -storepass {{_PASS}} -alias mykey123 -keypass {{_PASS}} -keyalg RSA -validity 36500

# zipalign -v -p 4 hoge.apk hoge_aligned.apk
export apk="$1"
echo "Signing $apk..."
apksigner.bat sign --ks '{{KEYSTORE_FILE}}' -v --v2-signing-enabled true --ks-pass pass:{{_PASS}} "$apk"

# Check the both fingerprints are the same
# keytool -list -v -keystore "C:\Users\rossning92\my-release-key.keystore" -storepass mykey123
# keytool -printcert -jarfile mykey123.apk

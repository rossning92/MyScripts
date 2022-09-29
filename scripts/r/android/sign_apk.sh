set -e

# Make a keystore file with keytool and check it
# keytool -genkey -v -keystore mykey123.keystore -storepass mykey123 -alias mykey123 -keypass mykey123 -keyalg RSA -validity 36500

# zipalign -v -p 4 hoge.apk hoge_aligned.apk
export apk="$1"
echo "Signing $apk..."
'C:\Android\android-sdk\build-tools\30.0.2\apksigner.bat' sign --ks '{{_KEY}}' -v --v2-signing-enabled true --ks-pass pass:{{_PASS}} "$apk"

# Check the both fingerprints are the same
# keytool -list -v -keystore "C:\Users\rossning92\my-release-key.keystore" -storepass mykey123
# keytool -printcert -jarfile mykey123.apk

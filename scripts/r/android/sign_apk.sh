set -e

# 3. make a kestore file with keytool and check it
# keytool -genkey -v -keystore mykey123.keystore -storepass mykey123 -alias mykey123 -keypass mykey123 -keyalg RSA -validity 36500

# cd 'C:\Users\rossning92\Downloads'

# 4. Sign a apk file with apksigner
# cd ~/Downloads/app/testflight
# 'C:\Android\android-sdk\build-tools\30.0.2\apksigner.bat' sign --ks "C:\Users\rossning92\my-release-key.keystore" -v --v2-signing-enabled true --ks-key-alias mykey123 --ks-pass pass:mykey123 mykey123.apk

# # 5. Check the both fingerprints are the same
# keytool -list -v -keystore "C:\Users\rossning92\my-release-key.keystore" -storepass mykey123
# keytool -printcert -jarfile mykey123.apk

# zipalign -v -p 4 hoge.apk hoge_aligned.apk
export apk=$(echo "$1" | sed -e 's/^\///' -e 's/\//\\/g' -e 's/^./\0:/')
echo "Signing $apk..."
'C:\Android\android-sdk\build-tools\30.0.2\apksigner.bat' sign --ks 'C:\Users\rossning92\my-release-key.keystore' -v --v2-signing-enabled true --ks-pass pass:123123 "$apk"

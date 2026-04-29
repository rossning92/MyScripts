defaults write com.apple.finder AppleShowAllFiles YES

# Disable auto-brightness (newer macOS, Catalina+)
defaults write com.apple.iokit.AmbientLightSensor "Automatic Display Enabled" -bool false
# Disable auto-brightness (older macOS, pre-Catalina)
defaults write com.apple.BezelServices dAuto -bool false

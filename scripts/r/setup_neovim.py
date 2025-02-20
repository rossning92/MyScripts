import os
import pathlib
import sys

# Calculate the realpath for the nvim configurations
nvim_config = (
    pathlib.Path(__file__).resolve().parent.parent.parent / "settings" / "nvim"
)

# Get symlink path
if sys.platform == "linux":
    # Ensure the .config directory exists
    config_path = pathlib.Path.home() / ".config"
    config_path.mkdir(parents=True, exist_ok=True)

    # Create a symlink for the nvim configuration
    symlink_path = config_path / "nvim"
    if symlink_path.exists() or symlink_path.is_symlink():
        symlink_path.unlink()  # Remove existing file or symlink
else:
    symlink_path = os.path.expandvars("%LOCALAPPDATA%\\nvim")

# Create symlink
os.symlink(nvim_config, symlink_path)

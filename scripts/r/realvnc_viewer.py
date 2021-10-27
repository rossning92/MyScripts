from _shutil import start_process

if __name__ == "__main__":
    VNC_VIEWER = r"C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe"
    start_process(
        [
            VNC_VIEWER,
            "{{VNC_SERVER}}",
            "-WarnUnencrypted=0",
            "-PasswordStoreOffer=1",
            "-FullScreen=1",
        ]
    )


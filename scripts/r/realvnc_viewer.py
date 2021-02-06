from _shutil import *

VNC_VIEWER = r"C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe"

if not exists(VNC_VIEWER):
    run_elevated('choco install vnc-viewer -y')

start_process(VNC_VIEWER)
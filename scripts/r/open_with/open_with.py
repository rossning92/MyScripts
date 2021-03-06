import json
import os
import subprocess
import sys
import traceback
from unittest import expectedFailure

import _appmanager
from _shutil import run_elevated

assoc = {
    ".3g2": ["mpv", "VLC"],
    ".3gp": ["mpv", "VLC"],
    ".3gp2": ["mpv", "VLC"],
    ".3gpp": ["mpv", "VLC"],
    ".4-win-x64": ["PathAdd"],
    ".aac": ["mpv", "VLC"],
    ".abnf": ["vscode", "notepad++"],
    ".ac3": ["mpv", "VLC"],
    ".aco": ["vscode", "notepad++"],
    ".ahk": ["vscode", "notepad++"],
    ".ai": ["AI"],
    ".aliases": ["vscode", "notepad++"],
    ".amr": ["mpv", "VLC"],
    ".amv": ["mpv", "VLC"],
    ".ape": ["mpv", "VLC"],
    ".ase": ["vscode", "notepad++"],
    ".asf": ["mpv", "VLC"],
    ".asp": ["vscode", "notepad++"],
    ".ass": ["mpv", "VLC"],
    ".asset": ["vscode", "notepad++"],
    ".asx": ["mpv", "VLC"],
    ".au3": ["vscode", "notepad++"],
    ".avi": ["mpv", "VLC"],
    ".bak": ["vscode", "notepad++"],
    ".bash_profile": ["vscode", "notepad++"],
    ".bashrc": ["vscode", "notepad++"],
    ".bat": ["vscode", "notepad++"],
    ".bib": ["vscode", "notepad++"],
    ".bin": ["HxD"],
    ".bind": ["vscode", "notepad++"],
    ".bmp": ["IrfanView"],
    ".bnf": ["vscode", "notepad++"],
    ".c": ["vscode", "notepad++"],
    ".c_": ["vscode", "notepad++"],
    ".cbp": ["vscode", "notepad++"],
    ".cfg": ["vscode", "notepad++"],
    ".cl7": ["vscode", "notepad++"],
    ".classpath": ["vscode", "notepad++"],
    ".cls": ["vscode", "notepad++"],
    ".cmake": ["vscode", "notepad++"],
    ".cmd": ["vscode", "notepad++"],
    ".cmdline": ["vscode", "notepad++"],
    ".cnf": ["vscode", "notepad++"],
    ".conf": ["vscode", "notepad++"],
    ".conffiles": ["vscode", "notepad++"],
    ".config": ["vscode", "notepad++"],
    ".conv": ["vscode", "notepad++"],
    ".cpp": ["vscode", "notepad++"],
    ".cps": ["vscode", "notepad++"],
    ".crash": ["vscode", "notepad++"],
    ".crdownload": ["mpv", "VLC"],
    ".crt": ["vscode", "notepad++"],
    ".cs": ["vscode", "notepad++"],
    ".cson": ["vscode", "notepad++"],
    ".css": ["vscode", "notepad++"],
    ".csv": ["notepad++", "tad"],
    ".cu": ["vscode", "notepad++"],
    ".cue": ["mpv", "VLC"],
    ".cxx": ["vscode", "notepad++"],
    ".dat": ["mpv", "VLC"],
    ".dbml": ["vscode", "notepad++"],
    ".def": ["vscode", "notepad++"],
    ".desktop": ["vscode", "notepad++"],
    ".divx": ["mpv", "VLC"],
    ".dll": ["PathAdd"],
    ".dmskm": ["mpv", "VLC"],
    ".dng": ["IrfanView"],
    ".docx": ["LibreOfficeWriter"],
    ".downloading": ["mpv", "VLC"],
    ".dpg": ["mpv", "VLC"],
    ".dpl": ["mpv", "VLC"],
    ".driveignore": ["vscode", "notepad++"],
    ".dropbox": ["vscode", "notepad++"],
    ".dtapart": ["mpv", "VLC"],
    ".dts": ["mpv", "VLC"],
    ".dtshd": ["mpv", "VLC"],
    ".dvr-ms": ["mpv", "VLC"],
    ".dxf": ["vscode", "notepad++"],
    ".dot": ["vscode", "notepad++"],
    ".eac3": ["mpv", "VLC"],
    ".efu": ["vscode", "notepad++"],
    ".ejs": ["vscode", "notepad++"],
    ".el": ["vscode", "notepad++"],
    ".emacs": ["vscode", "notepad++"],
    ".emf": ["vscode", "notepad++"],
    ".eml": ["vscode", "notepad++"],
    ".env": ["vscode", "notepad++"],
    ".eps": ["vscode", "notepad++"],
    ".epub": ["SumatraPDF", "adobereader"],
    ".erb": ["vscode", "notepad++"],
    ".evo": ["mpv", "VLC"],
    ".exe": ["PathAdd"],
    ".f4v": ["mpv", "VLC"],
    ".ffs_batch": ["vscode", "notepad++"],
    ".ffs_gui": ["vscode", "notepad++"],
    ".flac": ["mpv", "VLC"],
    ".flv": ["mpv", "VLC"],
    ".frag": ["vscode", "notepad++"],
    ".gif": ["IrfanView"],
    ".git-credentials": ["vscode", "notepad++"],
    ".gitconfig": ["vscode", "notepad++"],
    ".gitignore": ["vscode", "notepad++"],
    ".gradle": ["vscode", "notepad++"],
    ".grid": ["vscode", "notepad++"],
    ".h": ["vscode", "notepad++"],
    ".h_": ["vscode", "notepad++"],
    ".hpp": ["vscode", "notepad++"],
    ".htk": ["vscode", "notepad++"],
    ".htm": ["vscode", "notepad++"],
    ".html": ["vscode", "notepad++"],
    ".hxx": ["vscode", "notepad++"],
    ".i": ["vscode", "notepad++"],
    ".ico": ["IrfanView"],
    ".idc": ["vscode", "notepad++"],
    ".idx": ["mpv", "VLC"],
    ".ifo": ["mpv", "VLC"],
    ".iim": ["vscode", "notepad++"],
    ".iml": ["vscode", "notepad++"],
    ".index": ["vscode", "notepad++"],
    ".inf": ["vscode", "notepad++"],
    ".info": ["vscode", "notepad++"],
    ".ini": ["vscode", "notepad++"],
    ".inl": ["vscode", "notepad++"],
    ".ino": ["vscode", "notepad++"],
    ".ipynb": ["vscode", "notepad++"],
    ".iso": ["mpv", "VLC"],
    ".iss": ["vscode", "notepad++"],
    ".itf": ["vscode", "notepad++"],
    ".jade": ["vscode", "notepad++"],
    ".java": ["vscode", "notepad++"],
    ".jpeg": ["IrfanView"],
    ".jpg": ["IrfanView"],
    ".js": ["vscode", "notepad++"],
    ".json": ["vscode", "notepad++"],
    ".jsonlz4": ["vscode", "notepad++"],
    ".jsx": ["vscode", "notepad++"],
    ".k3g": ["mpv", "VLC"],
    ".keystore": ["vscode", "notepad++"],
    ".launch": ["vscode", "notepad++"],
    ".less": ["vscode", "notepad++"],
    ".list": ["vscode", "notepad++"],
    ".lmp4": ["mpv", "VLC"],
    ".lnk": ["HxD"],
    ".log": ["vscode", "notepad++"],
    ".lrc": ["vscode", "notepad++"],
    ".lyx": ["vscode", "notepad++"],
    ".lua": ["vscode", "notepad++"],
    ".m1a": ["mpv", "VLC"],
    ".m1v": ["mpv", "VLC"],
    ".m2a": ["mpv", "VLC"],
    ".m2t": ["mpv", "VLC"],
    ".m2ts": ["mpv", "VLC"],
    ".m2v": ["mpv", "VLC"],
    ".m3u": ["mpv", "VLC"],
    ".m3u8": ["mpv", "VLC"],
    ".m4a": ["mpv", "VLC"],
    ".m4b": ["mpv", "VLC"],
    ".m4p": ["mpv", "VLC"],
    ".m4v": ["mpv", "VLC"],
    ".manifest": ["vscode", "notepad++"],
    ".markdown": ["vscode", "notepad++"],
    ".mat": ["vscode", "notepad++"],
    ".md": ["vscode", "notepad++"],
    ".mdt": ["vscode", "notepad++"],
    ".meta": ["vscode", "notepad++"],
    ".mf": ["vscode", "notepad++"],
    ".mk": ["vscode", "notepad++"],
    ".mka": ["mpv", "VLC"],
    ".mkd": ["vscode", "notepad++"],
    ".mkv": ["mpv", "VLC"],
    ".mod": ["mpv", "VLC"],
    ".modules": ["vscode", "notepad++"],
    ".mov": ["mpv", "VLC"],
    ".mp2": ["mpv", "VLC"],
    ".mp2v": ["mpv", "VLC"],
    ".mp3": ["mpv", "ocenaudio"],
    ".mp4": ["mpv", "VLC"],
    ".mpa": ["mpv", "VLC"],
    ".mpc": ["mpv", "VLC"],
    ".mpe": ["mpv", "VLC"],
    ".mpeg": ["mpv", "VLC"],
    ".mpg": ["mpv", "VLC"],
    ".mpl": ["mpv", "VLC"],
    ".mpls": ["mpv", "VLC"],
    ".mpv2": ["mpv", "VLC"],
    ".mqv": ["mpv", "VLC"],
    ".ms11": ["vscode", "notepad++"],
    ".mtl": ["vscode", "notepad++"],
    ".mts": ["mpv", "VLC"],
    ".npy": ["vscode", "notepad++"],
    ".nsh": ["vscode", "notepad++"],
    ".nsi": ["vscode", "notepad++"],
    ".nsr": ["mpv", "VLC"],
    ".nsv": ["mpv", "VLC"],
    ".obj": ["vscode", "notepad++"],
    ".ods": ["LibreOfficeWriter"],
    ".odt": ["LibreOfficeWriter"],
    ".ogg": ["mpv", "ocenaudio"],
    ".ogm": ["mpv", "VLC"],
    ".ogv": ["mpv", "VLC"],
    ".org": ["vscode", "notepad++"],
    ".out": ["vscode", "notepad++"],
    ".p12": ["vscode", "notepad++"],
    ".pac": ["vscode", "notepad++"],
    ".pak": ["vscode", "notepad++"],
    ".part": ["mpv", "VLC"],
    ".pbtxt": ["vscode", "notepad++"],
    ".pcap": ["vscode", "notepad++"],
    ".pde": ["vscode", "notepad++"],
    ".pdf": ["SumatraPDF", "adobereader"],
    ".pem": ["vscode", "notepad++"],
    ".pgc": ["vscode", "notepad++"],
    ".php": ["vscode", "notepad++"],
    ".pkl": ["vscode", "notepad++"],
    ".pl": ["vscode", "notepad++"],
    ".plantuml": ["vscode", "notepad++"],
    ".pls": ["mpv", "VLC"],
    ".png": ["IrfanView"],
    ".ppm": ["IrfanView"],
    ".ppo": ["vscode", "notepad++"],
    ".prefs": ["vscode", "notepad++"],
    ".pri": ["vscode", "notepad++"],
    ".pro": ["vscode", "notepad++"],
    ".project": ["vscode", "notepad++"],
    ".properties": ["vscode", "notepad++"],
    ".props": ["vscode", "notepad++"],
    ".ps1": ["vscode", "notepad++"],
    ".psm1": ["vscode", "notepad++"],
    ".pub": ["vscode", "notepad++"],
    ".pxd": ["vscode", "notepad++"],
    ".py": ["vscode", "notepad++"],
    ".pyd": ["vscode", "notepad++"],
    ".pyx": ["vscode", "notepad++"],
    ".qsv": ["mpv", "VLC"],
    ".qtpotp": ["mpv", "VLC"],
    ".r": ["vscode", "notepad++"],
    ".ram": ["mpv", "VLC"],
    ".rapotp": ["mpv", "VLC"],
    ".rb": ["vscode", "notepad++"],
    ".record": ["vscode", "notepad++"],
    ".reg": ["vscode", "notepad++"],
    ".res": ["vscode", "notepad++"],
    ".rmpotp": ["mpv", "VLC"],
    ".rmvb": ["mpv", "VLC"],
    ".rpm": ["mpv", "VLC"],
    ".script": ["vscode", "notepad++"],
    ".sdirs": ["vscode", "notepad++"],
    ".sgy": ["vscode", "notepad++"],
    ".sh": ["vscode", "notepad++"],
    ".shader": ["vscode", "notepad++"],
    ".skm": ["mpv", "VLC"],
    ".sln": ["vscode", "notepad++"],
    ".smali": ["vscode", "notepad++"],
    ".smi": ["mpv", "VLC"],
    ".sql": ["vscode", "notepad++"],
    ".srt": ["vscode", "notepad++"],
    ".ssa": ["mpv", "VLC"],
    ".sub": ["mpv", "VLC"],
    ".sublime-menu": ["vscode", "notepad++"],
    ".sublime-package": ["vscode", "notepad++"],
    ".sublime-settings": ["vscode", "notepad++"],
    ".svg": ["IrfanView"],
    ".swf": ["mpv", "VLC"],
    ".tak": ["mpv", "VLC"],
    ".td": ["mpv", "VLC"],
    ".tdl": ["mpv", "VLC"],
    ".tex": ["vscode", "notepad++"],
    ".tif": ["IrfanView"],
    ".tiff": ["IrfanView"],
    ".tmlanguage": ["vscode", "notepad++"],
    ".tmpreferences": ["vscode", "notepad++"],
    ".tp": ["vscode", "notepad++"],
    ".tpl": ["vscode", "notepad++"],
    ".tppotp": ["mpv", "VLC"],
    ".tpr": ["mpv", "VLC"],
    ".trp": ["mpv", "VLC"],
    ".ts": ["vscode", "notepad++"],
    ".tspotp": ["mpv", "VLC"],
    ".tsv": ["vscode", "notepad++"],
    ".tud": ["mpv", "VLC"],
    ".txt": ["vscode", "notepad++"],
    ".ui": ["vscode", "notepad++"],
    ".user": ["vscode", "notepad++"],
    ".vbs": ["vscode", "notepad++"],
    ".vcf": ["vscode", "notepad++"],
    ".vcproj": ["vscode", "notepad++"],
    ".vcxproj": ["vscode", "notepad++"],
    ".vec": ["HxD"],
    ".vert": ["vscode", "notepad++"],
    ".vmx": ["vscode", "notepad++"],
    ".vob": ["mpv", "VLC"],
    ".wav": ["mpv", "ocenaudio"],
    ".wax": ["mpv", "VLC"],
    ".wdapk": ["vscode", "notepad++"],
    ".webm": ["mpv", "VLC"],
    ".wma": ["mpv", "VLC"],
    ".wmf": ["vscode", "notepad++"],
    ".wmp": ["mpv", "VLC"],
    ".wmpotp": ["mpv", "VLC"],
    ".wmv": ["mpv", "VLC"],
    ".wmx": ["mpv", "VLC"],
    ".wtv": ["mpv", "VLC"],
    ".wvpotp": ["mpv", "VLC"],
    ".wvx": ["mpv", "VLC"],
    ".x68": ["vscode", "notepad++"],
    ".xls": ["vscode", "notepad++"],
    ".xml": ["vscode", "notepad++"],
    ".xyz": ["vscode", "notepad++"],
    ".yaml": ["vscode", "notepad++"],
    ".yml": ["vscode", "notepad++"],
    ".zim": ["vscode", "notepad++"],
    ".zip": [["run_script", "/r/unzip.py"], "7zFM"],
    ".zxp": ["vscode", "notepad++"],
    ".gz": ["7zFM"],
    ".usf": ["vscode", "notepad++"],
    ".ush": ["vscode", "notepad++"],
    ".tar": ["7zFM"],
}


def open_with_hook(files, program_id):
    ext = os.path.splitext(files[0])[1].lower()

    # HACK: hijack extension handling
    if ext == ".vhd":
        run_elevated(["powershell", "-Command", "Mount-VHD -Path '%s'" % files])
        return True

    if program_id == 1 and ext in [".mp4", ".webm"]:
        from videoedit.video_editor import edit_video

        edit_video(files[0])

        return True

    return False


def open_with(files, program_id=0):
    if type(files) == str:
        files = [files]

    ext = os.path.splitext(files[0])[1].lower()

    if open_with_hook(files, program_id):
        return

    if ext not in assoc:
        raise Exception('Extension "%s" is not supported.' % ext)

    program = assoc[ext][program_id]

    if type(program) == str:
        executable = _appmanager.get_executable(program)
        assert executable is not None
        args = [executable] + files

    elif type(program) == list:
        args = program + files

    else:
        raise Exception("Unsupported program definition.")

    subprocess.Popen(args, close_fds=True)


if __name__ == "__main__":
    try:
        program_id = int(sys.argv[1])

        with open(os.path.join(os.environ["TEMP"], "ow_explorer_info.json")) as f:
            data = json.load(f)

        if data["current_folder"]:
            os.environ["_CUR_DIR"] = data["current_folder"]

        files = data["selected_files"]

        open_with(files, program_id)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        print(e)
        input("Press enter to exit...")

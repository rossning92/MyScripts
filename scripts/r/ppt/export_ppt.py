import os
import time
import subprocess

root = os.path.dirname(os.path.abspath(__file__))


def export_slide(file, index, export_shapes=False):
    mtime = os.path.getmtime(file)

    # Create output folder
    out_folder, _ = os.path.splitext(file)
    if not os.path.exists(out_folder):
        os.makedirs(out_folder, exist_ok=True)

    out_file = "%s/%03d.png" % (out_folder, index)
    if (not os.path.exists(out_file)) or (os.path.getmtime(out_file) < mtime):
        args = [
            "cscript",
            "//NoLogo",
            os.path.join(root, "export_slides.vbs"),
            file,
            "/i:%d" % index,
        ]
        if export_shapes:
            args.append("/shape")
        subprocess.check_call(args)

    return out_file


def export_video(file):
    mtime = os.path.getmtime(file)

    out_file = "%s.mp4" % os.path.splitext(file)[0]
    if (not os.path.exists(out_file)) or (os.path.getmtime(out_file) < mtime):
        print("Exporting %s..." % out_file)
        subprocess.check_call(["cscript", os.path.join(root, "export_video.vbs"), file])

    return out_file

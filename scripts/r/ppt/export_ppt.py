import win32com.client
import os
import time


app = None


def _open_ppt(file):
    global app
    if app is None:
        app = win32com.client.Dispatch("PowerPoint.Application")

    return app.Presentations.Open(os.path.abspath(file), True, False, False)


def export_slides(file, indices):
    assert indices is None or type(indices) in (list, tuple)
    assert file is not None

    ppt = None
    mtime = os.path.getmtime(file)

    # Create output folder
    out_folder, _ = os.path.splitext(file)
    if not os.path.exists(out_folder):
        os.makedirs(out_folder, exist_ok=True)

    # Export slides
    out_files = []
    for i in indices:
        out_file = "%s/%04d.png" % (out_folder, i + 1)
        if (not os.path.exists(out_file)) or (os.path.getmtime(out_file) < mtime):
            print("Exporting %s..." % out_file)

            if ppt is None:  # Lazy load
                ppt = _open_ppt(file)

                # Get slide size
                w = ppt.PageSetup.SlideWidth
                h = ppt.PageSetup.SlideHeight
                w = int(w / h * 1080)
                h = 1080

            ppt.Slides[i].Export(os.path.abspath(out_file), "PNG", w, h)

        out_files.append(out_file)

    return out_files


def export_video(file):
    mtime = os.path.getmtime(file)

    out_file = "%s.mp4" % os.path.splitext(file)[0]
    if (not os.path.exists(out_file)) or (os.path.getmtime(out_file) < mtime):
        print("Exporting %s..." % out_file)

        ppt = _open_ppt(file)

        ppt.CreateVideo(
            os.path.abspath(out_file),
            True,  # UseTimingsAndNarrations
            0,  # DefaultSlideDuration
            1080,  # VertResolution
            60,  # FramesPerSecond
            100,  # Quality
        )

        # Wait to be finished
        while ppt.CreateVideoStatus == 1:  # ppMediaTaskStatusInProgress
            time.sleep(0.1)

    return out_file


if __name__ == "__main__":
    export_video(
        r"C:\Users\Ross\Google Drive\KidslogicVideo\ep27\slide\player-control.pptx"
    )

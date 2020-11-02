import win32com.client
import os


def _get_ppt(file=None):
    app = win32com.client.Dispatch("PowerPoint.Application")
    if file is None:
        ppt = app.Presentations.Open(file, True, False, False)
    else:
        ppt = app.ActivePresentation
    return ppt


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
                ppt = _get_ppt(file)

                # Get slide size
                w = ppt.PageSetup.SlideWidth
                h = ppt.PageSetup.SlideHeight
                w = int(w / h * 1080)
                h = 1080

            ppt.Slides[i].Export(os.path.abspath(out_file), "PNG", w, h)

        out_files.append(out_file)

    return out_files


if __name__ == "__main__":
    export_slides(
        r"C:\Users\Ross\Google Drive\KidslogicVideo\ep27\slide\player-control.pptx", [0]
    )

from _shutil import *
from _term import *
from video_editor import edit_video

if __name__ == "__main__":
    os.chdir(os.environ["VIDEO_PROJECT_DIR"])

    new_file = wait_for_new_file(
        os.path.expandvars(r"%USERPROFILE%\Videos\**\*.mp4"), allow_exists=True
    )

    name = input("input file name (no ext): ")
    if not name:
        print2("Discard %s." % new_file, color="red")
        os.remove(new_file)

    else:
        name = "%d-%s" % (int(time.time()), slugify(name))
        os.makedirs("screencap", exist_ok=True)
        dest_file = "screencap/" + name + ".mp4"
        os.rename(new_file, dest_file)
        print2("file saved: %s" % dest_file, color="green")

        clip = "{" + "{ video('screencap/%s.mp4', na=True) }}" % name
        set_clip(clip)
        print("Clip is set to: %s" + clip)
        edit_video(os.path.abspath(dest_file))


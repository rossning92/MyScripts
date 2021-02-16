from _shutil import *
import datetime


def start_app(pkg, use_monkey=False):
    if use_monkey:
        args = [
            "adb",
            "shell",
            "monkey -p %s -c android.intent.category.LAUNCHER 1" % pkg,
        ]
        print("> " + " ".join(args))
        with open(os.devnull, "w") as fnull:
            ret = subprocess.call(args, stdout=fnull, stderr=fnull,)
        if ret != 0:
            raise Exception(
                'Launch package "%s" failed. Please check if it is installed.' % pkg
            )
    else:
        args = f'adb shell "dumpsys package | grep -i {pkg}/ | grep Activity"'
        out = subprocess.check_output(args, shell=True)
        out = out.decode().strip()
        lines = out.splitlines()
        line = lines[0].strip()
        id, pkg_activity = line.split()
        print("> ActivityName: " + pkg_activity)
        args = "adb shell am start -n %s" % pkg_activity
        print("> " + args)
        call2(args)


def clear_logcat():
    print("Clearing logcat...")

    # Retry on error
    while True:
        try:
            subprocess.check_call(["adb", "logcat", "-c"])
            break
        except subprocess.CalledProcessError:
            print("WARNING: clear logcat failed. Retrying...")


def kill_app(pkg):
    args = "adb shell am force-stop %s" % pkg
    call_echo(args)


def restart_app(pkg, use_monkey=True):
    print("Stop app: " + pkg)
    args = "adb shell am force-stop %s" % pkg
    print("> " + args)
    call2(args)

    start_app(pkg, use_monkey=use_monkey)


def restart_current_app():
    out = (
        subprocess.check_output(
            "adb shell \"dumpsys activity activities | grep -E 'mFocusedActivity|mResumedActivity'\"",
            shell=True,
        )
        .decode()
        .strip()
    )
    match = re.search(r"\{([^}]+)\}", out).group(1)
    pkg_activity = match.split()[2]
    pkg, activity = pkg_activity.split("/")

    call2("adb shell am force-stop %s" % pkg)
    call2("adb shell am start -n %s" % pkg_activity)


def logcat(
    proc_name=None,
    highlight=None,
    filter_str=None,
    clear=False,
    show_log_after_secs=-2,
    level=None,
    exclude=None,
    exclude_proc=None,
):
    call2("adb wait-for-device")

    if level:
        level = re.compile(level)
    if exclude:
        exclude = re.compile(exclude)
    if filter_str:
        filter_str = re.compile(filter_str)
    if exclude_proc:
        exclude_proc = re.compile(exclude_proc)
    if type(proc_name) == str:
        proc_name = re.compile(re.escape(proc_name))

    args = ["adb", "logcat", "-v", "brief"]

    if show_log_after_secs is not None:
        out = subprocess.check_output(
            ["adb", "shell", "date '+%m-%d %H:%M:%S'"], shell=True
        )
        out = out.decode().strip()
        dt_start = datetime.datetime.strptime(out, "%m-%d %H:%M:%S")
        dt_start += datetime.timedelta(seconds=show_log_after_secs)
        args += ["-T", dt_start.strftime("%m-%d %H:%M:%S") + ".000"]

    if clear:
        call2("adb logcat -c")

    if highlight is None:
        highlight = {}

    pid_map = {}
    last_proc = None

    LOGCAT_PATTERN = re.compile(r"^([A-Z])/([^\(]+)\(\s*(\d+)\):(.*)$")
    while True:
        try:
            for line in read_lines(args):
                match = re.match(LOGCAT_PATTERN, line)
                if match is None:
                    print(line)
                    continue

                lvl = match.group(1)
                tag = match.group(2)
                pid = int(match.group(3))
                message = match.group(4)

                # # Filter by time
                # if show_log_after_secs is not None:
                #     try:
                #         dt = datetime.datetime.strptime(line[:14].decode(), '%m-%d %H:%M:%S')
                #         if dt < dt_start:
                #             return None
                #     except:
                #         pass

                show_line = True

                # Filter by level
                if level and not re.search(level, lvl):
                    show_line = False

                # Filter by tag or message
                if filter_str and not re.search(filter_str, message):
                    show_line = False

                # Exclude by tag or message
                if exclude and (re.search(exclude, tag) or re.search(exclude, message)):
                    show_line = False

                # Get process name
                if pid not in pid_map:
                    out = subprocess.check_output(
                        "adb shell ps -p %d" % pid, universal_newlines=True
                    )
                    lines = out.splitlines()
                    if len(lines) == 1:
                        proc = None
                    else:
                        proc = out.split()[-1]
                    pid_map[pid] = proc
                else:
                    proc = pid_map[pid]

                if proc is not None:
                    # Filter by process name (include)
                    if proc_name and not re.search(proc_name, proc):
                        show_line = False

                    # Exclude by process name (exclude)
                    if exclude_proc and re.search(exclude_proc, proc):
                        show_line = False

                # HACK
                if "ROSS" in message:
                    show_line = True

                if show_line:
                    # Output process name
                    if last_proc != proc:
                        print2("%s (%d)" % (proc, pid))
                        last_proc = proc

                    lvl_text = " %s " % lvl
                    if lvl == "W":
                        print2(lvl_text, color="YELLOW", end="")
                    elif lvl == "E" or lvl == "F":
                        print2(lvl_text, color="RED", end="")
                    else:
                        print(lvl_text, end="")
                    print(": " + tag + ": " + message)
        except Exception as e:
            print(e)


def backup_pkg(pkg, out_dir=None, backup_user_data=False):
    if out_dir is not None:
        os.makedirs(out_dir, exist_ok=True)

    # Get apk path
    # 'package:/data/app/com.github.uiautomator-1AfatTFmPxzjNwUtT-5h7w==/base.apk'
    out = subprocess.check_output("adb shell pm path %s" % pkg)
    apk_path = out.decode().splitlines()[0]
    apk_path = apk_path.replace("package:", "")

    # Pull apk
    subprocess.call("adb pull %s %s.apk" % (apk_path, pkg), cwd=out_dir)

    # Check root permission
    if subprocess.call("adb shell type su") == 0:
        su = "su -c"
    else:
        su = ""

    if backup_user_data:
        print2("Backup app data...")
        subprocess.call(
            f"adb exec-out {su} tar -cf /sdcard/{pkg}.tar --exclude='data/data/{pkg}/cache' /data/data/{pkg}"
        )
        subprocess.call(f"adb pull /sdcard/{pkg}.tar", cwd=out_dir)
        subprocess.call(f"adb shell rm /sdcard/{pkg}.tar")

        print2("Backup obb...")
        subprocess.call(f"adb pull /sdcard/android/obb/{pkg}", cwd=out_dir)


def backup_directory(d, out_tar):
    temp_tar = "/data/local/tmp/backup.tar"
    subprocess.call(
        ["adb", "exec-out", f"tar -cf {temp_tar} {d}",]
    )
    subprocess.call(["adb", "pull", temp_tar, out_tar])
    subprocess.call(["adb", "shell", f"rm {temp_tar}"])


def screenshot(out_file=None):
    if out_file is None:
        src_file = datetime.datetime.now().strftime("Screenshot_%y%m%d%H%M%S.png")
    else:
        src_file = os.path.basename(out_file)

    print("Taking screenshot...")
    subprocess.check_call(["adb", "shell", "screencap -p /sdcard/%s" % src_file])
    subprocess.check_call(["adb", "pull", "-a", "/sdcard/%s" % src_file, out_file])
    subprocess.check_call(["adb", "shell", "rm /sdcard/%s" % src_file])


def get_active_pkg_and_activity():
    out = subprocess.check_output(
        [
            "adb",
            "shell",
            "dumpsys activity activities | grep -E 'mFocusedActivity|mResumedActivity'",
        ],
        universal_newlines=True,
    ).strip()
    match = re.search(r"\{([^}]+)\}", out).group(1)
    pkg_activity = match.split()[2]
    pkg, activity = pkg_activity.split("/")
    return pkg, activity


def get_device_name():
    out = subprocess.check_output(
        ["adb", "shell", "getprop", "ro.build.fingerprint"]
    ).decode()
    model = out.split("/")[1]
    return model


def take_screenshot(file_name=None):
    if not file_name:
        file_name = datetime.datetime.now().strftime("Screenshot_%y%m%d%H%M%S.png")

    print("Taking screenshot ...")
    subprocess.check_call(["adb", "shell", "screencap -p /sdcard/%s" % file_name])
    subprocess.check_call(["adb", "pull", "-a", "/sdcard/%s" % file_name])
    subprocess.check_call(["adb", "shell", "rm /sdcard/%s" % file_name])


def get_adk_path():
    ADK_SEARCH_PATH = [
        # Installed by choco
        r"C:\Android\android-sdk",
        # Default SDK path installed by Android Studio
        os.path.abspath(os.getenv("LOCALAPPDATA") + "/Android/Sdk"),
    ]

    for p in ADK_SEARCH_PATH:
        if os.path.exists(p):
            return p

    return None


def setup_android_env(ndk_version=None):
    env = os.environ

    # ANDROID_HOME
    android_home = get_adk_path()
    if android_home is None:
        raise Exception("Cannot find ANDROID_HOME")
    print2("ANDROID_HOME: %s" % android_home)
    env["ANDROID_HOME"] = android_home

    # NDK
    ndk_path = None
    if (ndk_version is not None) and (android_home is not None):
        match = glob.glob(os.path.join(android_home, "ndk", "%s*" % ndk_version))
        if match:
            ndk_path = match[0]

    if (android_home is not None) and (ndk_path is None):
        p = os.path.join(android_home, "ndk-bundle")
        if exists(p):
            ndk_path = p

    if (android_home is not None) and (ndk_path is None):
        found = sorted(list(glob.glob(os.path.join(android_home, "ndk/*"))))
        if found:
            ndk_path = found[-1]

    if ndk_path:
        print2("ANDROID_NDK_HOME: %s" % ndk_path)
        env["ANDROID_NDK_HOME"] = ndk_path
        env["ANDROID_NDK"] = ndk_path
        env["ANDROID_NDK_ROOT"] = ndk_path
        env["NDKROOT"] = ndk_path
        env["NDK_ROOT"] = ndk_path

        print(open(ndk_path + "/source.properties").read())

    # Setup PATH
    path = [
        env["ANDROID_HOME"] + "/platform-tools",
        env["ANDROID_HOME"] + "/tools",
        env["ANDROID_HOME"] + "/tools/bin",
        env["ANDROID_HOME"] + "/ndk-bundle",
    ]

    # JDK
    jdk_list = sorted(glob.glob(r"C:\Program Files\Java\jdk*"))
    if len(jdk_list) == 0:
        raise Exception("Cannot find JDK")
    jdk_path = jdk_list[-1] + "\\bin"  # Choose latest JDK
    print2("JDK_HOME: %s" % jdk_path)
    path.append(jdk_path)

    # Android build tools (latest)
    path_list = sorted(glob.glob(env["ANDROID_HOME"] + "\\build-tools\\*"))
    if len(path_list) > 0:
        print2("Android SDK: build-tools: " + path_list[-1])
        path.append(path_list[-1])

    prepend_to_path(path)


def adb_shell(command, check=True, **kwargs):
    print('EXEC: adb shell "%s"' % command)
    subprocess.run(["adb", "shell", command], check=check, **kwargs)


def wait_until_boot_complete():
    call_echo("adb wait-for-device")
    while True:
        try:
            if (
                subprocess.check_output(
                    ["adb", "shell", "getprop", "sys.boot_completed"],
                    universal_newlines=True,
                ).strip()
                == "1"
            ):
                break

            print(".", end="", flush=True)
            time.sleep(2)

        except Exception as e:
            print(e)
            time.sleep(2)


def adb_shell2(command, check=True, root=True):
    if root and not hasattr(adb_shell2, "super_su"):
        # Check root permission
        adb_shell2.super_su = subprocess.call("adb shell type su") == 0
        if not adb_shell2.super_su:
            subprocess.check_call(["adb", "root"])

    if adb_shell2.super_su:
        command = "su -c " + command

    subprocess.run(["adb", "shell", command], check=check)


def pm_list_packages():
    s = check_output("adb shell pm list packages").decode()
    s = s.replace("package:", "")
    lines = s.splitlines()
    lines = sorted(lines)
    return lines


def adb_install(file):
    print("Installing %s" % file)
    try:
        subprocess.check_output(
            [
                "adb",
                "install",
                "-r",  # Replace existing apps without clearing data
                "-d",  # Allow downgrade
                file,
            ],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        msg = e.output.decode()
        match = re.search("INSTALL_FAILED_UPDATE_INCOMPATIBLE: Package ([^ ]+)", msg)
        if match is not None:
            pkg = match.group(1)
            print("[INSTALL_FAILED_UPDATE_INCOMPATIBLE] Uninstalling %s..." % pkg)
            subprocess.call(["adb", "uninstall", pkg])
            subprocess.check_call(["adb", "install", "-r", file])


def adb_install2(file):
    """
    Install + restore app data.
    """
    adb_install(file)

    # Push data
    tar_file = os.path.splitext(file)[0] + ".tar"
    pkg = os.path.splitext(os.path.basename(file))[0]
    if exists(tar_file):
        print("Restore data...")
        call(f'adb push "{tar_file}" /data/local/tmp/')
        adb_shell2(f"tar -xf /data/local/tmp/{pkg}.tar", root=True)

        out = check_output(f"adb shell dumpsys package {pkg} | grep userId")
        out = out.decode().strip()

        userId = re.findall(r"userId=(\d+)", out)[0]
        print(f"Change owner of {pkg} => {userId}")
        adb_shell2(f"chown -R {userId}:{userId} /data/data/{pkg}", root=True)

        print("Reset SELinux perms")
        adb_shell2(f"restorecon -R /data/data/{pkg}", root=True)

    # Push obb file
    obb_folder = os.path.splitext(file)[0]
    if os.path.isdir(obb_folder):
        print("Push obb...")
        call2(f'adb push "{obb_folder}" /sdcard/android/obb')


def sample_proc_stat():
    adb_shell(
        """
    rm /data/local/tmp/proc_stat.txt
    total_secs=60
    while [ $total_secs -gt 0 ]; do
        cat /proc/stat >> /data/local/tmp/proc_stat.txt
        echo --- >> /data/local/tmp/proc_stat.txt
        echo $total_secs

        let total_secs=$total_secs-1
        sleep 1
    done
    """
    )

    call2("adb pull /data/local/tmp/proc_stat.txt")


def get_pkg_name_apk(file):
    setup_android_env()
    print("Start the app...")
    out = subprocess.check_output(["aapt", "dump", "badging", file]).decode()
    package_name = re.search("package: name='(.*?)'", out).group(1)
    print("PackageName: %s" % package_name)
    # activity_name = re.search("launchable-activity: name='(.*?)'", out).group(1)
    # print('LaunchableActivity: %s' % activity_name)
    return package_name


def run_apk(file):
    try:
        pkg = get_pkg_name_apk(file)
        start_app(pkg)
        return pkg
    except:
        print("Cannot launch the app")


def unlock_device(pin):
    out = subprocess.check_output(
        ["adb", "shell", 'dumpsys power | grep "mWakefulness="'],
        universal_newlines=True,
    )

    if "Dozing" in out:
        adb_shell("input keyevent 82")
        sleep(1)

        # Swipe up
        adb_shell("input touchscreen swipe 930 880 930 380")
        sleep(1)

        # Type pin
        adb_shell("input text %s" % pin)
        adb_shell("input keyevent KEYCODE_ENTER")

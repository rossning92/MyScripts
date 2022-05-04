import datetime
import glob
import logging
import os
import re
import subprocess
import sys
import threading
import time

from _shutil import call2, call_echo, check_output, prepend_to_path, print2, proc_lines

logger = logging.getLogger(__name__)


def reset_debug_sysprops():
    subprocess.check_call(["adb", "root"])
    try:
        lines = subprocess.check_output(
            ["adb", "shell", "getprop -Z | grep :debug_oculus_prop:"],
            universal_newlines=True,
        ).splitlines()

        for line in lines:
            line = line.strip()
            matches = re.findall(r"^\[(.*?)\]", line)
            prop_name = matches[0]

            logger.debug("Reset %s" % prop_name)
            adb_shell("setprop %s ''" % prop_name)
    except Exception as ex:
        logging.error(ex)


def start_app(pkg, use_monkey=False):
    if use_monkey:
        args = [
            "adb",
            "shell",
            "monkey -p %s -c android.intent.category.LAUNCHER 1" % pkg,
        ]
        logger.debug("shell_cmd: %s" % " ".join(args))
        with open(os.devnull, "w") as fnull:
            ret = subprocess.call(
                args,
                stdout=fnull,
                stderr=fnull,
            )
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
        _, pkg_activity = line.split()
        logger.debug("ActivityName=" + pkg_activity)
        args = ["adb", "shell", "am start -n %s" % pkg_activity]
        logger.debug("shell_cmd: %s" % " ".join(args))
        out = subprocess.check_output(args, universal_newlines=True)
        logger.debug(out)


def clear_logcat():
    logger.debug("Clearing logcat...")

    # Retry on error
    while True:
        try:
            subprocess.check_call(["adb", "logcat", "-c"])
            break
        except subprocess.CalledProcessError:
            logger.debug("WARNING: clear logcat failed. Retrying...")


def kill_app(pkg):
    args = "adb shell am force-stop %s" % pkg
    call_echo(args)


def restart_app(pkg, use_monkey=True):
    logger.debug("Stop app: " + pkg)
    args = "adb shell am force-stop %s" % pkg
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
    pkg, _ = pkg_activity.split("/")

    call2("adb shell am force-stop %s" % pkg)
    call2("adb shell am start -n %s" % pkg_activity)


def logcat(
    pkg=None,
    highlight=None,
    regex=None,
    clear=False,
    show_log_after_secs=-2,
    level=None,
    exclude=None,
    exclude_proc=None,
    ignore_duplicates=True,
):
    LOGCAT_PATTERN = re.compile(r"^([A-Z])/(.+?)\(\s*(\d+)\):\s?(.*)$")

    call2("adb wait-for-device")

    last_message = None
    dulicated_messages = 0

    if level:
        level = re.compile(level)
    if exclude:
        exclude = re.compile(exclude)
    if regex:
        regex = re.compile(regex)
    if exclude_proc:
        exclude_proc = re.compile(exclude_proc)
    if type(pkg) == str:
        pkg = re.compile(re.escape(pkg))

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

    while True:
        try:
            for line in proc_lines(args):
                match = re.match(LOGCAT_PATTERN, line)
                if match is None:
                    logger.debug(line)
                    continue

                lvl = match.group(1)
                tag = match.group(2)
                pid = int(match.group(3))
                message = match.group(4)

                if pid <= 0:
                    continue

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
                if regex and not re.search(regex, message):
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
                    if pkg and not re.search(pkg, proc):
                        show_line = False

                    # Exclude by process name (exclude)
                    if exclude_proc and re.search(exclude_proc, proc):
                        show_line = False

                # Always show lines if following conditions are met.
                if "ROSS:" in message:
                    show_line = True

                if not show_line:
                    continue

                if ignore_duplicates and message == last_message:
                    dulicated_messages += 1
                    print("\r(%d) " % dulicated_messages, end="")
                    continue

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

                last_message = message
                dulicated_messages = 0

        except Exception as ex:
            print2(ex)


def get_apk_path(pkg):
    out = subprocess.check_output(
        ["adb", "shell", "pm path %s" % pkg], universal_newlines=True
    )
    apk_path = out.splitlines()[0]
    apk_path = apk_path.replace("package:", "")
    return apk_path


def backup_pkg(pkg, out_dir=None, backup_user_data=False, backup_obb=True):
    if out_dir is not None:
        os.makedirs(out_dir, exist_ok=True)

    # Get apk path
    # 'package:/data/app/com.github.uiautomator-1AfatTFmPxzjNwUtT-5h7w==/base.apk'
    apk_path = get_apk_path(pkg)

    # Pull apk
    subprocess.check_call("adb pull %s %s.apk" % (apk_path, pkg), cwd=out_dir)

    # Check root permission
    if subprocess.call("adb shell type su") == 0:
        su = "su -c"
    else:
        su = ""

    if backup_user_data:
        logging.info("Backup app data...")
        subprocess.call(
            f"adb exec-out {su} tar -cf /sdcard/{pkg}.tar --exclude='data/data/{pkg}/cache' /data/data/{pkg}"
        )
        subprocess.call(f"adb pull /sdcard/{pkg}.tar", cwd=out_dir)
        subprocess.call(f"adb shell rm /sdcard/{pkg}.tar")

    if backup_obb:
        logging.info("Backup obb...")
        subprocess.call(f"adb pull /sdcard/android/obb/{pkg}", cwd=out_dir)


def adb_tar(d, out_tar):
    temp_tar = "/data/local/tmp/backup.tar"
    subprocess.check_call(
        [
            "adb",
            "exec-out",
            f"tar -cf {temp_tar} {d}",
        ]
    )
    subprocess.check_call(["adb", "pull", temp_tar, out_tar])
    subprocess.check_call(["adb", "shell", f"rm {temp_tar}"])


def adb_untar(tar_file):
    subprocess.check_call(["adb", "push", tar_file, "/data/local/tmp/"])
    adb_shell(f"tar -xf /data/local/tmp/{tar_file}")


def screenshot(out_file=None, scale=None):
    from _image import scale_image

    if out_file is None:
        out_file = datetime.datetime.now().strftime("Screenshot_%y%m%d%H%M%S.png")
        src_file = os.path.basename(out_file)
    else:
        os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
        src_file = os.path.basename(out_file)

    while True:
        try:
            logger.info("Taking screenshot...")
            subprocess.check_call(
                ["adb", "shell", "screencap -p /sdcard/%s" % src_file]
            )
            logger.debug(["adb", "pull", "-a", "/sdcard/%s" % src_file, out_file])
            subprocess.check_call(
                ["adb", "pull", "-a", "/sdcard/%s" % src_file, out_file]
            )
            subprocess.check_call(["adb", "shell", "rm /sdcard/%s" % src_file])

            break
        except subprocess.CalledProcessError:
            logger.debug("Retry after 1 second...")
            time.sleep(1)

    if scale is not None:
        scale_image(out_file, scale, scale)
    return out_file


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


def get_adk_path():
    if sys.platform == "win32":
        ADK_SEARCH_PATH = [
            # Installed by choco
            r"C:\Android\android-sdk",
            # Default SDK path installed by Android Studio
            os.path.abspath(os.getenv("LOCALAPPDATA") + "/Android/Sdk"),
        ]

        for p in ADK_SEARCH_PATH:
            if os.path.exists(p):
                return p
    else:
        pass

    return None


def get_prop(name):
    return (
        subprocess.check_output(["adb", "shell", "getprop %s" % name]).decode().strip()
    )


def setup_jdk(jdk_version=None):
    # JDK
    jdk_list = sorted(glob.glob(r"C:\Program Files\Java\jdk*"))
    if len(jdk_list) == 0:
        raise Exception("Cannot find JDK")
    if jdk_version:
        java_home = [x for x in jdk_list if ("%s" % jdk_version) in x][-1]
    else:
        java_home = jdk_list[-1]  # Choose latest JDK

    os.environ["JAVA_HOME"] = java_home
    logging.debug("JAVA_HOME: %s" % java_home)

    jdk_bin = java_home + "\\bin"
    prepend_to_path(jdk_bin)


def setup_android_env(env=None, ndk_version=None, jdk_version=None):
    if env is None:
        env = os.environ

    path = []

    # ANDROID_HOME
    android_home = get_adk_path()
    if android_home is None:
        raise Exception("Cannot find ANDROID_HOME")
    logging.info("ANDROID_HOME: %s" % android_home)
    env["ANDROID_HOME"] = android_home
    path += [
        env["ANDROID_HOME"] + "/platform-tools",
        env["ANDROID_HOME"] + "/tools",
        env["ANDROID_HOME"] + "/tools/bin",
        env["ANDROID_HOME"] + "/ndk-bundle",
    ]

    # build-tools
    build_tools_dir = sorted(glob.glob(env["ANDROID_HOME"] + "/build-tools/*"))
    if len(build_tools_dir) > 0:
        path.append(build_tools_dir[-1])

    # NDK
    ndk_path = None
    if (android_home is not None) and (ndk_path is None):
        found = sorted(glob.glob(os.path.join(android_home, "ndk", "*")))
        if found:
            ndk_path = found[-1]

    if (android_home is not None) and (ndk_path is None):
        p = os.path.join(android_home, "ndk-bundle")
        if os.path.exists(p):
            ndk_path = p

    if (android_home is not None) and (ndk_path is None):
        found = sorted(list(glob.glob(os.path.join(android_home, "ndk/*"))))
        if found:
            ndk_path = found[-1]

    if ndk_path:
        logging.info("ANDROID_NDK_ROOT: %s" % ndk_path)
        env["ANDROID_NDK_ROOT"] = ndk_path
        env["ANDROID_NDK_HOME"] = ndk_path
        env["ANDROID_NDK"] = ndk_path
        env["NDKROOT"] = ndk_path
        env["NDK_ROOT"] = ndk_path
        path.append(ndk_path)

    setup_jdk(jdk_version=jdk_version)

    # Android build tools (latest)
    path_list = sorted(glob.glob(env["ANDROID_HOME"] + "\\build-tools\\*"))
    if len(path_list) > 0:
        logging.info("Android SDK: build-tools: " + path_list[-1])
        path.append(path_list[-1])

    prepend_to_path(path, env=env)


def adb_shell(command, check=True, check_output=False, echo=False, **kwargs):
    logger.debug('shell_cmd: adb shell "%s"' % command)

    if echo:
        print2('> adb shell "%s"' % command)

    if check_output:
        return subprocess.check_output(
            ["adb", "shell", command], universal_newlines=True
        )
    else:
        return subprocess.run(["adb", "shell", command], check=check, **kwargs)


def wait_for_device():
    call_echo("adb wait-for-device")


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

        except Exception as ex:
            logging.error(ex)
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


def adb_install(apk, force=False):
    if not force:
        # Get package name
        out = subprocess.check_output(
            ["aapt", "dump", "badging", apk], universal_newlines=True
        )
        match = re.search(r"package: name='(.+?)'", out)
        pkg_name = match.group(1)
        logger.debug("apk package name: %s" % pkg_name)

        should_install = False
        if not app_is_installed(pkg_name):
            logger.info("App does not exist on device, installing...")
            should_install = True

        if not should_install:
            # Get local apk size in bytes
            local_file_size = os.path.getsize(apk)

            # Get file size in bytes
            apk_path_device = get_apk_path(pkg_name)
            file_size = int(
                subprocess.check_output(
                    ["adb", "shell", "wc -c %s | awk '{print $1}'" % apk_path_device],
                    universal_newlines=True,
                )
            )

            if local_file_size != file_size:
                logger.info(
                    "Installed APK size does not match with local file %d != %d, reinstalling..."
                    % (file_size, local_file_size)
                )
                should_install = True

    if force or should_install:
        logger.info("Installing %s" % apk)
        try:
            args = [
                "adb",
                "install",
                "-r",  # Replace existing apps without clearing data
                "-d",  # Allow downgrade
                apk,
            ]
            logging.debug("%s" % args)
            subprocess.check_output(
                args,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as ex:
            msg = ex.output.decode()
            match = re.search(
                "INSTALL_FAILED_UPDATE_INCOMPATIBLE: Package ([^ ]+)", msg
            )
            if match is not None:
                pkg = match.group(1)
                logging.warn(
                    "[INSTALL_FAILED_UPDATE_INCOMPATIBLE] Uninstalling %s..." % pkg
                )
                subprocess.check_call(["adb", "uninstall", pkg])
                subprocess.check_call(["adb", "install", "-r", apk])
            else:
                raise ex
    else:
        logger.info("App already installed, skipping...")

    return pkg_name


def adb_install2(file):
    """
    Install + restore app data.
    """
    adb_install(file)

    # Push data
    tar_file = os.path.splitext(file)[0] + ".tar"
    pkg = os.path.splitext(os.path.basename(file))[0]
    if os.path.exists(tar_file):
        logger.info("Restoring app data...")
        subprocess.check_call(["adb", "push", "tar_file}", "/data/local/tmp/"])
        adb_shell2(f"tar -xf /data/local/tmp/{pkg}.tar", root=True)

        out = check_output(f"adb shell dumpsys package {pkg} | grep userId")
        out = out.decode().strip()

        userId = re.findall(r"userId=(\d+)", out)[0]
        logger.info(f"Changing owner of {pkg} => {userId}")
        adb_shell2(f"chown -R {userId}:{userId} /data/data/{pkg}", root=True)

        logger.info("Resetting SELinux permisions...")
        adb_shell2(f"restorecon -R /data/data/{pkg}", root=True)

    # Push obb file
    obb_folder = os.path.splitext(file)[0]
    if os.path.isdir(obb_folder):
        logger.info("Pushing obb...")
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
    logger.info("Starting the app...")
    out = subprocess.check_output(["aapt", "dump", "badging", file]).decode()
    package_name = re.search("package: name='(.*?)'", out).group(1)
    logger.debug("PackageName=%s" % package_name)
    # activity_name = re.search("launchable-activity: name='(.*?)'", out).group(1)
    # logger.debug('LaunchableActivity: %s' % activity_name)
    return package_name


def unlock_device(pin):
    out = subprocess.check_output(
        ["adb", "shell", 'dumpsys power | grep "mWakefulness="'],
        universal_newlines=True,
    )

    if "Dozing" in out:
        adb_shell("input keyevent 82")
        time.sleep(1)

        # Swipe up
        adb_shell("input touchscreen swipe 930 880 930 380")
        time.sleep(1)

        # Type pin
        adb_shell("input text %s" % pin)
        adb_shell("input keyevent KEYCODE_ENTER")


def is_locked():
    patt = re.compile("(?:mShowingLockscreen|isStatusBarKeyguard|showing)=(true|false)")
    m = patt.search(adb_shell("dumpsys window policy", check_output=True))
    if not m:
        raise Exception("Couldn't determine screen lock state")
    return m.group(1) == "true"


def app_is_installed(pkg_name):
    try:
        subprocess.check_output(
            ["adb", "shell", "pm", "path", pkg_name],
            universal_newlines=True,
        )
    except Exception:
        return False
    return True


def logcat_bg(patt):
    """Show filtered logcat in a background thread."""

    if type(patt) != str:
        raise Exception("patt must be a string")

    patt = re.compile(patt)

    def logcat_thread():
        while True:
            print("logcat begin.", end="\r\n")

            for line in proc_lines(
                [
                    "adb",
                    "logcat",
                ]
            ):
                if re.search(patt, line):
                    print2(line, end="\r\n", color="black")

            print("logcat end.", end="\r\n")
            time.sleep(1)

    threading.Thread(
        target=logcat_thread,
        daemon=True,  # daemon threads will terminate as main thread exits
    ).start()


def toggle_prop(name, values=("0", "1")):
    cur_val = subprocess.check_output(
        ["adb", "shell", "getprop %s" % name], universal_newlines=True
    ).strip()

    # Find next value
    try:
        i = values.index(cur_val)
    except ValueError:
        i = 0
    new_val = values[(i + 1) % len(values)]

    command = "setprop %s %s" % (name, new_val)
    logger.debug(command)
    subprocess.check_call(["adb", "shell", command])


def run_apk(apk):
    pkg_name = adb_install(apk)
    restart_app(pkg_name)


def set_android_serial_by_product_name(product):
    lines = subprocess.check_output(["adb", "devices"], universal_newlines=True).split(
        "\n"
    )[1:]

    for line in lines:
        if not line.strip():
            continue
        serial = line.split("\t")[0]

        product_ = subprocess.check_output(
            ["adb", "-s", serial, "shell", "getprop", "ro.build.product"],
            universal_newlines=True,
        ).strip()

        if product_ == product:
            os.environ["ANDROID_SERIAL"] = serial
            logging.info("Set ANDROID_SERIAL to %s" % serial)
            return True

    raise Exception("Couldn't find device with product name %s" % product)


def setprop(prop):
    """Set all system properities in a single shell command."""

    shell = ""
    for k, v in prop.items():
        if not v:
            v = "''"
        shell += "setprop {} {};".format(k, v)
    adb_shell(shell)


def select_app_pkg():
    from _term import Menu

    s = subprocess.check_output(
        ["adb", "shell", "pm list packages"], universal_newlines=True
    )
    s = s.replace("package:", "")
    lines = s.splitlines()
    lines = sorted(lines)
    i = Menu(items=lines).exec()
    if i == -1:
        return None
    else:
        return lines[i]

# https://github.com/baldurk/renderdoc/search?l=Python&q=ExecuteAndInject

import logging
import os
import threading
import time

import renderdoc as rd
from _android import get_device_name, get_main_activity
from _shutil import get_home_path, get_time_str, getch, setup_logger


def list_executables(remote):
    # GetHomeFolder() gives you a good default path to start with.
    # ListFolder() lists the contents of a folder and can recursively
    # browse the remote filesystem.
    home = remote.GetHomeFolder()
    paths = remote.ListFolder(home)
    logging.info(f"Executables in home folder '{home}':")
    for p in paths:
        logging.info("  - " + p.filename)


def main():
    # This sample is intended as an example of how to do remote capture and replay
    # as well as using device protocols to automatically enumerate remote targets.
    #
    # It is not complete since it requires filling in with custom logic to select
    # the executable and trigger the capture at the desired time
    # raise RuntimeError("This sample should not be run directly, read the source")

    rd.InitialiseReplay(rd.GlobalEnvironment(), [])

    protocols = rd.GetSupportedDeviceProtocols()
    logging.info(f"Supported device protocols: {protocols}")

    protocol_to_use = "adb"

    # the protocol must be supported
    if protocol_to_use not in protocols:
        raise RuntimeError(f"{protocol_to_use} protocol not supported")

    protocol = rd.GetDeviceProtocolController(protocol_to_use)

    devices = protocol.GetDevices()

    if len(devices) == 0:
        raise RuntimeError(f"no {protocol_to_use} devices connected")

    if "ANDROID_SERIAL" in os.environ:
        device = os.environ["ANDROID_SERIAL"]
    else:
        # Choose the first device
        device = devices[0]

    name = protocol.GetFriendlyName(device)
    logging.info(f"Running test on {device} - {name}")

    url = protocol.GetProtocolName() + "://" + device

    # Protocols can enumerate devices which are not supported. Capture/replay
    # is not guaranteed to work on these devices
    if not protocol.IsSupported(url):
        raise RuntimeError(f"{device} doesn't support capture/replay - too old?")

    # Protocol devices may be single-use and not support multiple captured programs
    # If so, trying to execute a program for capture is an error
    if not protocol.SupportsMultiplePrograms(url):
        # check to see if anything is running. Just use the URL
        ident = rd.EnumerateRemoteTargets(url, 0)

        if ident != 0:
            logging.info(f"{name} already has a program running on {ident}")
            # raise RuntimeError(f"{name} already has a program running on {ident}")

    while True:
        try:
            # Let's try to connect
            result, remote = rd.CreateRemoteServerConnection(url)

            if result == rd.ResultCode.NetworkIOFailed and protocol is not None:
                # If there's just no I/O, most likely the server is not running. If we have
                # a protocol, we can try to start the remote server
                logging.info("Couldn't connect to remote server, trying to start it")

                result = protocol.StartRemoteServer(url)

                if result != rd.ResultCode.Succeeded:
                    raise RuntimeError(
                        f"Couldn't launch remote server, got error {str(result)}"
                    )

            break

        except RuntimeError as ex:
            logging.warn(f"Error on connection: {ex}")
            logging.info("Try to connect again")

    assert remote is not None

    # We now have a remote connection. This works regardless of whether it's a device
    # with a protocol or not. In fact we are done with the protocol at this point
    logging.info("Got connection to remote server")
    protocol = None

    # list_executables(remote)

    # Select your executable, perhaps hardcoded or browsing using the above
    # functions
    pkg_name = os.environ["PKG_NAME"]

    exe = os.environ.get("START_ACTIVITY")
    if not exe:
        exe = get_main_activity(pkg_name)

    workingDir = ""
    cmdLine = ""
    env = []
    opts = rd.GetDefaultCaptureOptions()

    logging.info(f"Start {exe}")

    result = remote.ExecuteAndInject(exe, workingDir, cmdLine, env, opts)

    if result.result != rd.ResultCode.Succeeded:
        remote.ShutdownServerAndConnection()
        raise RuntimeError(f"Couldn't launch {exe}, got error {str(result.result)}")

    # Spin up a thread to keep the remote server connection alive while we make a capture,
    # as it will time out after 5 seconds of inactivity
    def ping_remote(remote, kill):
        success = True
        while success and not kill.is_set():
            success = remote.Ping()
            time.sleep(1)

    kill = threading.Event()
    ping_thread = threading.Thread(target=ping_remote, args=(remote, kill))
    ping_thread.start()

    # Create target control connection
    target = rd.CreateTargetControl(url, result.ident, "remote_capture.py", True)

    if target is None:
        kill.set()
        ping_thread.join()
        remote.ShutdownServerAndConnection()
        raise RuntimeError(f"Couldn't connect to target control for {exe}")

    logging.info("Connected to remote server.")

    # TODO: Wait for the capture condition we want
    # capture_condition()

    run_wait_secs = 15
    if os.environ.get("RUN_WAIT_SECS"):
        run_wait_secs = int(os.environ.get("RUN_WAIT_SECS"))
    if run_wait_secs < 0:
        print("(press enter to trigger capture...)")
        getch()
    else:
        logging.info(f"Wait for {run_wait_secs} seconds, then capture a frame.")
        time.sleep(run_wait_secs)

    logging.info("Trigger capture")
    target.TriggerCapture(1)

    # Pump messages, keep waiting until we get a capture message. Time out after 30 seconds
    msg = None
    start = time.clock()
    while msg is None or msg.type != rd.TargetControlMessageType.NewCapture:
        msg = target.ReceiveMessage(None)

        if time.clock() - start > 30:
            break

    # Close the target connection, we're done either way
    target.Shutdown()
    target = None

    # Stop the background ping thread
    kill.set()
    ping_thread.join()

    # If we didn't get a capture, error now
    if msg.type != rd.TargetControlMessageType.NewCapture:
        remote.ShutdownServerAndConnection()
        raise RuntimeError(
            "Didn't get new capture notification after triggering capture"
        )

    cap_path = msg.newCapture.path
    cap_id = msg.newCapture.captureId

    logging.info(
        f"Got new capture at {cap_path} which is frame {msg.newCapture.frameNumber} with {msg.newCapture.api}"
    )

    # We could save the capture locally
    local_file = os.path.join(
        get_home_path(),
        "Desktop",
        f"{pkg_name}-{get_device_name()}-{get_time_str()}.rdc",
    )
    logging.info(f"Save capture to {local_file}")
    remote.CopyCaptureFromRemote(
        cap_path,
        local_file,
        None,
    )


if __name__ == "__main__":
    setup_logger()
    main()

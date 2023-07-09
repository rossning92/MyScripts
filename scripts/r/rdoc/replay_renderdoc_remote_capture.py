# https://github.com/baldurk/renderdoc/search?l=Python&q=ExecuteAndInject

import logging
import os
import subprocess

import numpy as np
import renderdoc as rd

cap_path_local = os.environ["RDC_FILE"]
file = os.path.basename(cap_path_local)
name, _ = os.path.splitext(file)
cap_path = "/data/local/tmp/" + file
args = ["adb", "push", cap_path_local, cap_path]
print(args)
subprocess.check_call(args)

controller = None


def init():
    global controller

    rd.InitialiseReplay(rd.GlobalEnvironment(), [])

    protocols = rd.GetSupportedDeviceProtocols()
    print(f"Supported device protocols: {protocols}")

    protocol_to_use = "adb"

    # the protocol must be supported
    if protocol_to_use not in protocols:
        raise RuntimeError(f"{protocol_to_use} protocol not supported")

    protocol = rd.GetDeviceProtocolController(protocol_to_use)

    devices = protocol.GetDevices()

    if len(devices) == 0:
        raise RuntimeError(f"no {protocol_to_use} devices connected")

    dev = None
    # Choose the first device
    for dev in devices:
        if dev == os.environ["ANDROID_SERIAL"]:
            break
    name = protocol.GetFriendlyName(dev)

    print(f"Running test on {dev} - named {name}")

    URL = protocol.GetProtocolName() + "://" + dev

    # Protocols can enumerate devices which are not supported. Capture/replay
    # is not guaranteed to work on these devices
    if not protocol.IsSupported(URL):
        raise RuntimeError(f"{dev} doesn't support capture/replay - too old?")

    # Protocol devices may be single-use and not support multiple captured programs
    # If so, trying to execute a program for capture is an error
    if not protocol.SupportsMultiplePrograms(URL):
        # check to see if anything is running. Just use the URL
        ident = rd.EnumerateRemoteTargets(URL, 0)

        if ident != 0:
            print(f"{name} already has a program running on {ident}")
            # raise RuntimeError(f"{name} already has a program running on {ident}")

    # Let's try to connect
    result, remote = rd.CreateRemoteServerConnection(URL)

    if result == rd.ResultCode.NetworkIOFailed and protocol is not None:
        # If there's just no I/O, most likely the server is not running. If we have
        # a protocol, we can try to start the remote server
        print("Couldn't connect to remote server, trying to start it")

        result = protocol.StartRemoteServer(URL)

        if result != rd.ResultCode.Succeeded:
            raise RuntimeError(
                f"Couldn't launch remote server, got error {str(result)}"
            )

        # Try to connect again!
        result, remote = rd.CreateRemoteServerConnection(URL)

    if result != rd.ResultCode.Succeeded:
        raise RuntimeError(
            f"Couldn't connect to remote server, got error {str(result)}"
        )

    # We now have a remote connection. This works regardless of whether it's a device
    # with a protocol or not. In fact we are done with the protocol at this point
    protocol = None

    print("Got connection to remote server")

    # Open a replay. It's recommended to set no proxy preference, but you could
    # call remote.LocalProxies and choose an index.
    #
    # The path must be remote - if the capture isn't freshly created then you need
    # to copy it with remote.CopyCaptureToRemote()
    print("opening capture")
    result, controller = remote.OpenCapture(
        rd.RemoteServer.NoPreference, cap_path, rd.ReplayOptions(), None
    )
    print("capture opened")

    if result != rd.ResultCode.Succeeded:
        remote.ShutdownServerAndConnection()
        raise RuntimeError(f"Couldn't open {cap_path}, got error {str(result)}")

    # We can now use replay as normal.
    #
    # The replay is tunnelled over the remote connection, so you don't have to keep
    # pinging the remote connection while using the controller. Use of the remote
    # connection and controller can be interleaved though you should only access
    # them from one thread at once. If they are both unused for 5 seconds though,
    # the timeout will happen, so if the controller is idle it's advisable to ping
    # the remote connection


for i in range(3):
    try:
        init()
        break
    except Exception as ex:
        pass

actions = {}


# Define a recursive function for iterating over actions
def iterDraw(d, indent=""):
    global actions

    # save the action by eventId
    actions[d.eventId] = d

    # Iterate over the draw's children
    for d in d.children:
        iterDraw(d, indent + "    ")


def replay(controller):
    # Iterate over all of the root actions, so we have names for each
    # eventId
    for d in controller.GetRootActions():
        iterDraw(d)

    # Enumerate the available counters
    counters = controller.EnumerateCounters()

    # Describe each counter
    for c in counters:
        desc = controller.DescribeCounter(c)

        logging.debug("Counter %d (%s):" % (c, desc.name))
        logging.debug("    %s" % desc.description)
        logging.debug(
            "    Returns %d byte %s, representing %s"
            % (desc.resultByteWidth, desc.resultType, desc.unit)
        )

    if not (rd.GPUCounter.EventGPUDuration in counters):
        raise RuntimeError("Implementation doesn't support Samples Passed counter")

    # Get the description for the counter we want
    eventGPUDurationDesc = controller.DescribeCounter(rd.GPUCounter.EventGPUDuration)
    # print(eventGPUDurationDesc.name, eventGPUDurationDesc.description)

    # Now we fetch the counter data, this is a good time to batch requests of as many
    # counters as possible, the implementation handles any book keeping.
    results = controller.FetchCounters([rd.GPUCounter.EventGPUDuration])

    # Look in the results for any draws with 0 samples written - this is an indication
    # that if a lot of draws appear then culling could be better.
    # print(results)
    total_gpu_duration = 0.0
    for r in results:
        draw = actions[r.eventId]

        # # Only care about draws, not about clears and other misc events
        # if not (draw.flags & rd.ActionFlags.Drawcall):
        #     continue

        # if eventGPUDurationDesc.resultType == float:
        val = r.value.d

        logging.debug(
            "%.4f ms: EID %d '%s' had EventGPUDuration"
            % (val * 1000, r.eventId, draw.GetName(controller.GetStructuredFile()))
        )

        total_gpu_duration += val
    logging.debug("Total GPU: %.4f ms" % (total_gpu_duration * 1000))
    return total_gpu_duration


total_gpu_duration = []
for i in range(20):
    total_gpu_duration.append(replay(controller))
mean = np.mean(total_gpu_duration)

print("result_csv: %s,%.4f" % (name, mean * 1000))

controller.Shutdown()

# We can still use remote here - e.g. capture again, replay something else,
# save the capture, etc

# remote.ShutdownServerAndConnection()

rd.ShutdownReplay()

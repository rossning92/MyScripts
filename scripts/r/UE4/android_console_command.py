from _shutil import *

commands = {
    'r': 'vr.HeadTracking.Reset',
    'm': 'ke * MoveCameraEvent',
}

# Engine\Build\Android\Java\src\com\epicgames\ue4\ConsoleCmdReceiver.java
while True:
    for k, v in commands.items():
        print('%s - %s' % (k, v))

    s = input()
    if s in commands:
        cmd = commands[s]
    else:
        cmd = s

    print('Run Command: %s' % cmd)

    args = f'''adb shell "am broadcast -a android.intent.action.RUN -e cmd '{cmd}'"'''
    call2(args)

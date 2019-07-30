from _shutil import *
from _term import *

commands = {
    'r': 'vr.HeadTracking.Reset',
    'm': 'ke * MoveCameraEvent',
    '[': 'vr.PixelDensity 0.1',
    ']': 'vr.PixelDensity 1.0',
}

# Engine\Build\Android\Java\src\com\epicgames\ue4\ConsoleCmdReceiver.java
while True:
    for k, v in commands.items():
        print('%s - %s' % (k, v))

    s = getch()
    if s in commands:
        cmd = commands[s]
    else:
        cmd = s

    print2('Run Command: %s' % cmd)

    args = f'''adb shell "am broadcast -a android.intent.action.RUN -e cmd '{cmd}'"'''
    call2(args)

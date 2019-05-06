from _shutil import *

# Engine\Build\Android\Java\src\com\epicgames\ue4\ConsoleCmdReceiver.java
while True:
    cmd = input()
    args = f'''adb shell "am broadcast -a android.intent.action.RUN -e cmd '{cmd}'"'''
    call(args)

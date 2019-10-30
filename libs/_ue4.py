from _shutil import *


def ue4_command(cmd):
    args = 'adb shell "am broadcast -a android.intent.action.RUN -e cmd \'%s\'"' % cmd
    call_echo(args)


def ue4_recenter():
    ue4_command('vr.HeadTracking.Reset')


def ue4_show_stat():
    ue4_command('stat unit')
    ue4_command('stat fps')

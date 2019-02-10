import os
import glob


def prepend_to_path(p):
    env['PATH'] = os.pathsep.join(p) + env['PATH']


env = os.environ

# Android-SDK
ADK_SEARCH_PATH = [
    r'C:\Android\android-sdk',
    os.path.abspath(os.getenv('LOCALAPPDATA') + '/Android/Sdk')
]

for p in ADK_SEARCH_PATH:
    if os.path.exists(p):
        env['ANDROID_HOME'] = p
        print('Set ANDROID_HOME to %s' % p)
        break

# NDK
env['ANDROID_NDK_HOME'] = \
    env['ANDROID_NDK_ROOT'] = \
    env['NDKROOT'] = \
    env['NDK_ROOT'] = \
    env['ANDROID_HOME'] + '/ndk-bundle'

# JDK
jdk_path = sorted(glob.glob(r'C:\Program Files\Java\jdk*'), reverse=True)[0]
env['PATH'] += os.pathsep + jdk_path + '\\bin'

path = [
    env['ANDROID_HOME'] + '/platform-tools',
    env['ANDROID_HOME'] + '/build-tools',
    env['ANDROID_HOME'] + '/tools',
]
prepend_to_path(path)

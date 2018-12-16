from subprocess import call

packages = [
    'platforms;android-21',
    'platforms;android-24',
    'build-tools;27.0.3',
    'lldb;3.1',
    'ndk-bundle'
]

for pkg in packages:
    call(['sdkmanager', pkg], shell=True)

from _shutil import *


def disable_ipv4():
    run_elevated('Disable-NetAdapterBinding -Name Wi-Fi -ComponentID ms_tcpip -PassThru')

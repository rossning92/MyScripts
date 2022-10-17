$ErrorActionPreference = "Stop"
Add-Type -Path "$PSScriptRoot\HidLibrary.dll"

function Enable-FunctionKeys {
    $HID_VENDOR_ID_LOGITECH = 0x046d
    $HID_DEVICE_ID_K380 = 0xb342 

    $K380_SEQ_FKEYS_ON = 0x10, 0xff, 0x0b, 0x1e, 0x00, 0x00, 0x00
    $K380_SEQ_FKEYS_OFF = 0x10, 0xff, 0x0b, 0x1e, 0x01, 0x00, 0x00

    $devices = [HidLibrary.HidDevices]::Enumerate($HID_VENDOR_ID_LOGITECH, $HID_DEVICE_ID_K380)
    $devices = $devices | Where-Object { $_.IsConnected -eq $true }

    foreach ($device in $devices) {
        $device.OpenDevice()
        $device.Write($K380_SEQ_FKEYS_ON) | Out-Null
        $device.CloseDevice()
    }
}

for (; ; ) {
    Enable-FunctionKeys
    Start-Sleep -Seconds 10
}

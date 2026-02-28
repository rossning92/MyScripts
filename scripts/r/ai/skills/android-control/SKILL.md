---
description: instructions for controlling Android phone
allow: termux-*
---

## Battery status

```bash
termux-battery-status
```

## Screen brightness

```bash
termux-brightness 128
```

## Torch / flashlight

```bash
termux-torch on
termux-torch off
```

## Volume control

```bash
termux-volume music 5
termux-volume alarm 7
```

## Get clipboard text

```bash
termux-clipboard-get
```

## Set clipboard text

```bash
echo "Hello world" | termux-clipboard-set
```

## Get location

```bash
termux-location
```

## Take photo

```bash
termux-camera-photo photo.jpg
```

## Record microphone (5 sec)

```bash
termux-microphone-record -d 5 audio.wav
```

## Play media

```bash
termux-media-player play song.mp3
```

## Text to speech

```bash
termux-tts-speak "Hello world"
```

## Call number

```bash
termux-telephony-call 123456789
```

## Send SMS

```bash
termux-sms-send -n 123456789 "Hello!"
```

## List SMS

```bash
termux-sms-list
```

## Call logs

```bash
termux-call-log
```

## Contacts

```bash
termux-contact-list
```

## Wi‑Fi info

```bash
termux-wifi-connectioninfo
```

## Enable / Disable Wi‑Fi

```bash
termux-wifi-enable true
termux-wifi-enable false
```

## Scan Wi‑Fi

```bash
termux-wifi-scaninfo
```

## Share text

```bash
echo "Hello" | termux-share
```

## Share file

```bash
termux-share file.txt
```

## Navigation

For navigation or finding locations:

```bash
termux-open "https://www.google.com/maps/dir/?api=1&destination=ADDRESS"
```

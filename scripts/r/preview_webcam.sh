if [[ -z "$WEBCAM_DEVICE" ]]; then
    WEBCAM_DEVICE=$(v4l2-ctl --list-devices | fzf | xargs)
    run_script ext/set_variable.py WEBCAM_DEVICE "$WEBCAM_DEVICE"
fi

mpv av://v4l2:$WEBCAM_DEVICE --profile=low-latency --untimed --demuxer-lavf-o=video_size=1920x1080,input_format=mjpeg

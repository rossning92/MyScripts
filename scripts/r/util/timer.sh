#!/bin/bash

time=0
while true; do
    hours=$((time / 3600))
    minutes=$((time / 60 % 60))
    seconds=$((time % 60))
    printf "%02d:%02d:%02d\n" $hours $minutes $seconds
    sleep 1
    ((time++))
done

adb root
adb shell "for f in \$(ls -t /data/tombstones/tombstone_* 2>/dev/null | head -n 5); do
    echo \"\n--- \$f ---\"
    grep -E 'Timestamp|>>>' \"\$f\"
    grep -E '#[0-9]+ pc' \"\$f\" | head -n 8
done"

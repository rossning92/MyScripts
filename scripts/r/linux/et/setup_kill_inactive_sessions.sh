#!/bin/bash

set -e

sudo tee "/usr/local/bin/kill_inactive_et_sessions.sh" >/dev/null <<'EOF'
#!/bin/bash

threshold_seconds=$((24 * 60 * 60))
inactive_pids=()

for pid in $(pgrep etterminal); do
    tty_index=$(grep -s "tty-index:" /proc/$pid/fdinfo/7 | awk '{print $2}')
    if [ -n "$tty_index" ]; then
        tty="/dev/pts/$tty_index"
        mtime=$(stat -c %Y "$tty" 2>/dev/null)
        if [ -n "$mtime" ]; then
            now=$(date +%s)
            idle=$((now - mtime))
            if [ "$idle" -ge "$threshold_seconds" ]; then
                inactive_pids+=("$pid")
            fi
        fi
    else
        inactive_pids+=("$pid")
    fi
done

if [ "${#inactive_pids[@]}" -gt 0 ]; then
    echo "Killing inactive et sessions: ${inactive_pids[*]}"
    kill "${inactive_pids[@]}" 2>/dev/null
fi
EOF

sudo chmod 755 "/usr/local/bin/kill_inactive_et_sessions.sh"

sudo mkdir -p "/etc/systemd/system"

sudo tee "/etc/systemd/system/kill-inactive-et-sessions.service" >/dev/null <<EOF
[Unit]
Description=Kill inactive et sessions

[Service]
Type=oneshot
ExecStart=/usr/local/bin/kill_inactive_et_sessions.sh
EOF

sudo tee "/etc/systemd/system/kill-inactive-et-sessions.timer" >/dev/null <<EOF
[Unit]
Description=Run kill inactive et sessions periodically

[Timer]
OnBootSec=5m
OnUnitActiveSec=1h
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now "kill-inactive-et-sessions.timer"

echo "Installed and started kill-inactive-et-sessions.timer"

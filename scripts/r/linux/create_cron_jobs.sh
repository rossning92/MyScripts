add_cron_job() {
    job="$1"
    (crontab -l 2>/dev/null | grep -Fxq "$job") || (echo "$(
        crontab -l 2>/dev/null
        echo "$job"
    )" | crontab -)
}

add_cron_job "*/1 * * * * echo \"hello world\" 2>&1 | /usr/bin/logger -t CRONOUTPUT"
add_cron_job "*/1 * * * * run_script r/gdrive/sync_gdrive.sh | /usr/bin/logger -t CRONOUTPUT"

crontab -l

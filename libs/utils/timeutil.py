from datetime import datetime


def time_diff_str(ts: float):
    cur_time = datetime.now()
    input_time = datetime.fromtimestamp(ts)
    time_diff = cur_time - input_time
    sec_diff = round(time_diff.total_seconds())
    abs_val = abs(sec_diff)

    if abs_val < 60:
        s = f"{abs_val}s"
    elif abs_val < 3600:
        minutes = abs_val // 60
        s = f"{minutes}m"
    elif abs_val < 86400:
        hours = abs_val // 3600
        s = f"{hours}h"
    else:
        days = abs_val // 86400
        s = f"{days}d"

    if sec_diff < 0:
        return f"+{s}"
    else:
        return f"-{s}"

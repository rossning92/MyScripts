from datetime import datetime


def time_diff_str(ts: float):
    cur_time = datetime.now()
    input_time = datetime.fromtimestamp(ts)
    time_diff = cur_time - input_time
    sec_diff = round(time_diff.total_seconds())
    abs_val = abs(sec_diff)

    if abs_val < 60:
        s = f"{abs_val} sec{'s' if abs_val != 1 else ''}"
    elif abs_val < 3600:
        minutes = abs_val // 60
        s = f"{minutes} min{'s' if minutes != 1 else ''}"
    elif abs_val < 86400:
        hours = abs_val // 3600
        s = f"{hours} hr{'s' if hours != 1 else ''}"
    else:
        days = abs_val // 86400
        s = f"{days} day{'s' if days != 1 else ''}"

    if sec_diff < 0:
        return f"in {s}"
    else:
        return f"{s} ago"

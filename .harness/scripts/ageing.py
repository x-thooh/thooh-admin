"""「过去了几天」只在这里算：两个时刻都是 epoch 秒，差值向下取整成整天。"""

from datetime import UTC, datetime, time


def age_days(since_ts, now_ts):
    return int((now_ts - since_ts) // 86400)


def day_ts(day):
    """date → 当天 UTC 零点的 epoch 秒。"""
    return datetime.combine(day, time.min, tzinfo=UTC).timestamp()

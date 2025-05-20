import time
from collections import deque
from typing import Deque

from .config import get_settings
from .logger import logger

_settings = get_settings()


class AnomalyDetector:
    def __init__(self, threshold: int = _settings.rate_threshold_per_minute):
        self.threshold = threshold
        self._timestamps: Deque[float] = deque(maxlen=1000)

    def record_request(self):
        now = time.time()
        self._timestamps.append(now)
        # prune >60s old
        while self._timestamps and self._timestamps[0] < now - 60:
            self._timestamps.popleft()
        if len(self._timestamps) > self.threshold:
            logger.warning(
                "High request rate detected: %s requests in last 60s",
                len(self._timestamps),
            )

    def record_401(self):
        logger.error(
            "Repeated 401 Unauthorized responses – possible credential misuse."
        )

import time
from collections import deque
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_reqs = 15):
        self.max_reqs = max_reqs
        self.req_times = deque()
        self.window = timedelta(minutes=1)
    
    def wait_if_needed(self):
        now = datetime.now()

        while self.req_times and (now - self.req_times[0]) > self.window:
            self.req_times.popleft()

        if len(self.req_times) >= self.max_reqs:
            sleep_time = (self.req_times[0] + self.window - now).total_seconds()
            if sleep_time > 0:
                print(f'Rate limit reached. Waiting for {sleep_time:.1f} seconds')

    def record_request(self):
        self.req_times.append(datetime.now())
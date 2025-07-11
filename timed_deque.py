import time
from collections import deque

class TimedDeque:
    def __init__(self, max_age_seconds):
        self.queue = deque()
        self.max_age = max_age_seconds

    def append(self, value):
        now = time.time()
        self.queue.append((now, value))
        self._purge_old()

    def get_items(self):
        self._purge_old()
        return [item for ts, item in self.queue]

    def _purge_old(self):
        now = time.time()
        while self.queue and (now - self.queue[0][0]) > self.max_age:
            self.queue.popleft()

if __name__ == '__main__':
    # 示例使用
    dq = TimedDeque(max_age_seconds=10)
    dq.append("A")
    time.sleep(5)
    dq.append("B")
    time.sleep(6)
    dq.append("C")
    print(dq.get_items())  # 输出只剩下 C
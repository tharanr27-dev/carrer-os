"""In-memory throttle for failed logins.

Two sliding windows: failures per (email, client IP) and failures per client IP. While a window is full the
login endpoint answers 429 *before* checking the password, so an attacker cannot tell a correct guess from a
wrong one. A successful login clears that (email, IP) counter.

Limits: state is per process (a multi-worker deployment needs a shared store such as Redis), and the client IP
is `request.client.host`. Behind a reverse proxy, run uvicorn with `--proxy-headers` and a trusted
`--forwarded-allow-ips`, otherwise every user appears to share the proxy's address.
"""

import math
import time
from collections import deque
from typing import Callable, Deque, Dict, Hashable

from fastapi import HTTPException, status

from app.core.config import settings


class LoginThrottle:
    def __init__(
        self,
        max_per_account: int = 5,
        max_per_ip: int = 30,
        window_seconds: float = 900,
        clock: Callable[[], float] = time.monotonic,
        max_keys: int = 10_000,
    ):
        self.max_per_account = max_per_account
        self.max_per_ip = max_per_ip
        self.window = window_seconds
        self.clock = clock
        self.max_keys = max_keys
        self._accounts: Dict[Hashable, Deque[float]] = {}
        self._ips: Dict[Hashable, Deque[float]] = {}

    def reset(self) -> None:
        self._accounts.clear()
        self._ips.clear()

    @staticmethod
    def _account_key(email: str, ip: str) -> tuple:
        return (email.strip().lower(), ip)

    def _live(self, store: Dict[Hashable, Deque[float]], key: Hashable, now: float) -> Deque[float]:
        dq = store.get(key)
        if dq is None:
            return deque()
        while dq and now - dq[0] >= self.window:
            dq.popleft()
        if not dq:
            store.pop(key, None)
        return dq

    def _retry_after(self, dq: Deque[float], limit: int, now: float) -> int:
        # The window frees up when the oldest counted failure ages out.
        return max(1, math.ceil(self.window - (now - dq[len(dq) - limit])))

    def check(self, email: str, ip: str) -> None:
        now = self.clock()
        acct = self._live(self._accounts, self._account_key(email, ip), now)
        ips = self._live(self._ips, ip, now)
        waits = []
        if len(acct) >= self.max_per_account:
            waits.append(self._retry_after(acct, self.max_per_account, now))
        if len(ips) >= self.max_per_ip:
            waits.append(self._retry_after(ips, self.max_per_ip, now))
        if waits:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Please wait before trying again.",
                headers={"Retry-After": str(max(waits))},
            )

    def _add(self, store: Dict[Hashable, Deque[float]], key: Hashable, now: float) -> None:
        if key not in store and len(store) >= self.max_keys:
            for k in [k for k in store if not self._live(store, k, now)]:  # purge expired first
                store.pop(k, None)
            if len(store) >= self.max_keys:
                store.pop(next(iter(store)))  # then evict the oldest entry
        store.setdefault(key, deque()).append(now)

    def record_failure(self, email: str, ip: str) -> None:
        now = self.clock()
        self._add(self._accounts, self._account_key(email, ip), now)
        self._add(self._ips, ip, now)

    def record_success(self, email: str, ip: str) -> None:
        self._accounts.pop(self._account_key(email, ip), None)


login_throttle = LoginThrottle(
    max_per_account=settings.LOGIN_MAX_FAILURES_PER_ACCOUNT,
    max_per_ip=settings.LOGIN_MAX_FAILURES_PER_IP,
    window_seconds=settings.LOGIN_FAILURE_WINDOW_SECONDS,
)

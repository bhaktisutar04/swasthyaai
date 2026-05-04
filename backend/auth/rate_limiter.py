from collections import defaultdict
from datetime import datetime, timedelta
import threading

MAX_ATTEMPTS = 5
WINDOW_MINUTES = 15

# Store timestamps of attempts for each email
_attempts = defaultdict(list)
_lock = threading.Lock()

def _cleanup_old_attempts(email: str, now: datetime):
    """Removes attempt timestamps that fall outside the current time window."""
    cutoff = now - timedelta(minutes=WINDOW_MINUTES)
    _attempts[email] = [t for t in _attempts[email] if t > cutoff]

def check_rate_limit(email: str) -> bool:
    """Returns True if the user is under the rate limit, False otherwise."""
    with _lock:
        now = datetime.now()
        _cleanup_old_attempts(email, now)
        return len(_attempts[email]) < MAX_ATTEMPTS

def record_attempt(email: str):
    """Records a new failed attempt for the user."""
    with _lock:
        now = datetime.now()
        _cleanup_old_attempts(email, now)
        _attempts[email].append(now)

def reset_attempts(email: str):
    """Clears attempts for the user after a successful login or reset."""
    with _lock:
        if email in _attempts:
            del _attempts[email]

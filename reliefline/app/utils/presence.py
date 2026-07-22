"""Real "currently online" presence — separate from User.is_active (an
admin-set account enable/disable flag) and from User.last_login (only moves
at sign-in). A user counts as online only while their session has produced a
request within ONLINE_THRESHOLD, per the before_request heartbeat in
app/__init__.py that stamps User.last_activity.
"""
from datetime import datetime, timedelta

ONLINE_THRESHOLD = timedelta(minutes=5)


def is_online(user):
    return bool(user and user.last_activity and datetime.utcnow() - user.last_activity <= ONLINE_THRESHOLD)

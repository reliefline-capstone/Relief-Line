# Online/Offline status of users.

from datetime import timedelta

from app.utils.timezone import ph_now

ONLINE_THRESHOLD = timedelta(minutes=5)


# Tells if a user was active in the last 5 minutes.
# Used for the green 'Online' badge on the System Admin pages.
def is_online(user):
    return bool(user and user.last_activity and ph_now() - user.last_activity <= ONLINE_THRESHOLD)

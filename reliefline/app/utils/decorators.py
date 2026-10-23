# Page access control by role.

from functools import wraps
from flask import abort
from flask_login import current_user

# Page lock by role: only users with one of the listed roles can open the page.
# Example: @role_required('pswdo_admin') means only PSWDO staff can see it.
def role_required(*roles):
    # Wraps a page with the role check.
    def decorator(f):
        # Runs the role check before the page opens.
        # If the user is not logged in or has the wrong role, a 'Forbidden' error is shown instead.
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                # Not allowed: show a 'Forbidden' page.
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator

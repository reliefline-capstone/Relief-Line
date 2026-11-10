# Friendly error pages (403 Forbidden, 404 Not Found, 500 Server Error, etc.) shown instead of Flask's plain text ones.

from flask import render_template
from werkzeug.exceptions import HTTPException

from app.extensions import db

# The title, explanation, and icon shown for each error code.
# Codes not listed here fall back to the general 'Something went wrong' wording.
ERROR_PAGES = {
    400: ("Bad Request", "The request couldn't be understood. Please check the form or link and try again.", "alert-triangle"),
    401: ("Login Required", "You need to log in to open this page.", "lock"),
    403: ("Access Forbidden", "You don't have permission to open this page. It may belong to a different office or role.", "shield"),
    404: ("Page Not Found", "The page or record you're looking for doesn't exist or may have been removed.", "search"),
    405: ("Action Not Allowed", "This page can't be used that way. Please go back and try again from the system's buttons.", "x-circle"),
    413: ("File Too Large", "The file you uploaded is bigger than the allowed size. Please choose a smaller file.", "file-text"),
    500: ("Something Went Wrong", "The system ran into a problem while loading this page. Please try again in a moment.", "alert-triangle"),
}


# Builds the error page for the given code, with buttons back to the user's dashboard or the login page.
# If the page itself fails to draw (e.g. the database is down), a plain text message is returned instead.
def _render_error(code):
    from flask_login import current_user
    from app.routes.auth import _dashboard_endpoint

    title, message, icon_name = ERROR_PAGES.get(code, ERROR_PAGES[500])
    try:
        logged_in = current_user.is_authenticated
        dashboard = _dashboard_endpoint(current_user.role) if logged_in else None
        return render_template(
            "errors/error.html",
            code=code, title=title, message=message, icon_name=icon_name,
            logged_in=logged_in, dashboard_endpoint=dashboard,
        ), code
    except Exception:
        return f"{code} {title} - {message}", code


# Turns on the friendly error pages for the whole app.
# Called once from create_app().
def register_error_handlers(app):

    # Shows the friendly page for any normal web error (403, 404, 405, 413, ...).
    @app.errorhandler(HTTPException)
    def _handle_http_error(e):
        # Redirects and other non-error codes pass through untouched.
        if e.code is None or e.code < 400:
            return e
        return _render_error(e.code)

    # Shows the 'Something went wrong' page when the code crashes.
    # Any half-finished database changes are cancelled first so the page can still load.
    @app.errorhandler(500)
    def _handle_server_error(e):
        db.session.rollback()
        return _render_error(500)

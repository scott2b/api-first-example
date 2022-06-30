"""
Simple session messages implementation. Requires that the request object
have a session. For most frameworks, this will be a dictionary-like session
set on the request object in session middleware.

Usage:

  * call add_message to add a session message to be displayed to the user

  * call clear_messages in the template after rendering out the current session
    messages
"""
from typing import List


def clear_messages(request, key=None):
    """Call from a template after rendering messages to clear out the current
    message list.
    """
    if key:
        key = f"messages__{key}"
    else:
        key = "messages"
    request.session[key] = []
    return ""


def add_message(request, message, key: str = None, classes: List[str] = None):
    """Add a message to the session messages list."""
    if key:
        key = f"messages__{key}"
    else:
        key = "messages"
    if not key in request.session:
        request.session[key] = []
    msg = {"text": message}
    if classes:
        msg["class"] = " ".join(classes)
    request.session[key].append(msg)


def add(*args, **kwargs):
    """An alias for add_message."""
    return add_message(*args, **kwargs)

"""
Custom template renderer that injects the request object into the context and
sets a clear_messages function on the request for session message handling.
"""
import inspect
import types
import jinja2
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from .messages import clear_messages


class Templates(Jinja2Templates):
    """Custom Template handler."""

    def TemplateResponse(self, name: str, context: dict, **kwargs):
        """Render a template response.

        If it exists and is not already set in the context, injects the
        request object from the calling scope into the template context.

        Adds a clear_request method to the request instance.
        """
        if "request" in context:
            req = context["request"]
            if isinstance(req, Request):
                req.clear_messages = types.MethodType(clear_messages, req)
        else:
            frame = inspect.currentframe()
            try:
                _locals = frame.f_back.f_locals
                req = _locals.get("request")
                if req is not None and isinstance(req, Request):
                    context["request"] = req
                    req.clear_messages = types.MethodType(clear_messages, req)
            finally:
                del frame
        return super().TemplateResponse(name, context, **kwargs)


render = Templates(directory="templates").TemplateResponse

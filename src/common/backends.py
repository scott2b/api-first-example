import base64
import copy
import datetime
from starlette.authentication import AuthenticationBackend, AuthCredentials
from starlette.authentication import SimpleUser
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from .models import User, OAuth2Token


# from cryptography.fernet import Fernet
# from common.config import settings

# csrf_secret = settings.CSRF_KEY

# def fernet(key: str) -> Fernet:
#    key = key + "=" * (len(key) % 4)
#    _key = base64.urlsafe_b64encode(base64.urlsafe_b64decode(key))
#    return Fernet(_key)
#
# def encrypt(data: str) -> bytes:
#    return fernet(csrf_secret).encrypt(data.encode())
#
# def decrypt(data: bytes) -> bytes:
#    return fernet(csrf_secret).decrypt(data)


# class CSRFMiddleware(BaseHTTPMiddleware):
#
#    async def dispatch(self, request, call_next):
#        """I have modeled this after Django's approach of putting the CSRF token in the
#        headers (see: https://docs.djangoproject.com/en/4.0/ref/csrf/#ajax) mainly
#        because Starlette does not let us access the request body in middleware
#        (see: https://github.com/encode/starlette/issues/495) but also because it is
#        better not to anyway. This is currently inconsistent with our forms handling,
#        where the CSRF token is included as hidden data in a form.
#        """
#        print("CSRF MIDDLEWARE", request.method)
#        print(request.headers)
#        print(request.scope)
#        print(dir(request.scope["auth"]))
#        print(request.scope["auth"].scopes)
#        print(dir(request))
#        print(request.base_url)
#        print(request.url)
#        #if request.method == "POST" and "application/json" in request.headers["content-type"].split(";"):
#        #    token = request.headers.get("x-csrftoken")
#        #    print("CSRF TOKEN", token.encode())
#        #    user_id = decrypt(token.encode())
#        #    print("USER ID:", user_id)
#        #request.scope["csrftoken"] = encrypt(str(request.user.id)).decode()
#        #print("GETTING RESPONSE")
#        response = await call_next(request)
#        print(request.headers)
#        #print("CSRF IN SCOPE:", request.scope["csrftoken"])
#        print("RETURNING RESPONSE")
#        return response


class SessionAuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        if "user_id" in request.session:
            user_id = request.session["user_id"]
            user = User.table[user_id]
            if user is None:  # something is wrong with the session data
                del request.session["user_id"]
                if "username" in request.session:
                    del request.session["username"]
                return None
            creds = ["app_auth", "api_auth"]
            if user.superuser:
                creds.append("admin_auth")
            return AuthCredentials(creds), user
        if request.headers.get("authorization"):
            bearer = request.headers["authorization"].split()
            if bearer[0] != "Bearer":
                return
            bearer = bearer[1]
            token = OAuth2Token.access_tokens.get(bearer)
            if token is None:
                return
            user = token.client.user
            if not user.active:
                return
            if token.access_token_expires_at < datetime.datetime.utcnow():
                return
            if token.revoked:
                return
            request.scope["token"] = token
            return AuthCredentials(["api_auth"]), user

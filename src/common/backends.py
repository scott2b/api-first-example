import datetime
from starlette.authentication import AuthenticationBackend, AuthCredentials
from .models import User, OAuth2Token


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

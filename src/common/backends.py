import copy
import datetime
from starlette.authentication import AuthenticationBackend, AuthCredentials
#from ..orm import oauth2token
#from ..orm.user import User
#from ..users.tables import User
from starlette.authentication import SimpleUser
#from piccolooauth2.tables import OAuth2Token, timestamp
from starlette.exceptions import HTTPException
from .models import User
from .database import OAuth2Token


class SessionAuthBackend(AuthenticationBackend):

    async def authenticate(self, request):
        print("auth middleware backend")
        print(request.session)
        if 'user_id' in request.session:
            print("user id in session")
            user_id = request.session['user_id']
            print("user id", user_id)
            #user = await User.objects().get(User.id == user_id)
            user = User.table[user_id]
            if user is None: # something is wrong with the session data
                print("something wrong with session data")
                del request.session["user_id"]
                if "username" in request.session:
                    del request.session["username"]
                return None
            creds = ['app_auth', 'api_auth']
            if user.superuser:
                creds.append('admin_auth')
            print("returning credentialed user with creds:", creds)
            return AuthCredentials(creds), user
        if request.headers.get('authorization'):
            bearer = request.headers['authorization'].split()
            print("bearer", bearer)
            if bearer[0] != 'Bearer':
                return
            bearer = bearer[1]
            #token = await OAuth2Token.objects().get( OAuth2Token.access_token == bearer )
            token = OAuth2Token[bearer]
            #if token is None or token.revoked:
            #    return # return without authorization
            #if datetime.datetime.utcnow() > token.access_token_expires_at:
            #    return # return without authorization
            #return AuthCredentials(['api_auth']), None
            if token.access_token_expires_at < timestamp():
                raise HTTPException(status_code=403, detail="Expired token")
            if token.revoked:
                raise HTTPException(status_code=403, detail="Invalid token")
            if token is None:
                raise HTTPException(status_code=403, detail="Invalid token")
            request.scope['token'] = token
            #return token
            return AuthCredentials(['api_auth']), None



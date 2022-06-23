from starlette.applications import Starlette
from starlette.authentication import requires
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from starlette.requests import Request
from starlette.routing import Route, Mount
from common.backends import SessionAuthBackend
from common.config import settings
from common.models import OAuth2Client
from .forms import LoginForm
from .templating import render
from . import messages



async def homepage(request:Request):
    return render('home.html', {})


async def login(request):
    data = await request.form()
    form = LoginForm(request, formdata=data, meta={ 'csrf_context': request.session })
    if request.method == 'POST':
        user = form.validate()
        print("validated user:", user)
        if user:
            request.session['username'] = user.username
            request.session['user_id'] = user.id
            print(request.session)
            next = request.query_params.get('next', '/')
            return RedirectResponse(url=next, status_code=302)
    return render('login.html', {
        'form': form,
    })


@requires("app_auth")
def logout(request):
    if "user_id" in request.session:
        del request.session["user_id"]
    if "username" in request.session:
        del request.session["username"]
    messages.add(request, "You are now logged out.", classes=["info"])
    return RedirectResponse(url="/")


@requires("app_auth")
def app_clients(request):
    print(OAuth2Client.table)
    clients = OAuth2Client.get_for_user(request.user)
    return render("apps.html", { "clients": clients })

@requires("app_auth")
def tasks(request):
    return render("tasks.html", {})


routes = [
    Route('/', homepage, name='home', methods=['GET', 'POST']),
    Route('/apps', app_clients, name='apps', methods=['GET']),
    Route('/login', login, name='login', methods=['GET', 'POST']),
    Route('/logout', logout, name='logout', methods=['GET']),
    Route('/tasks', tasks, name='tasks', methods=['GET'])
]

app = Starlette(
    debug=True,
    routes=routes
)

#if settings.ALLOWED_HOSTS:
#    app.add_middleware(
#        TrustedHostMiddleware,
#        allowed_hosts=settings.ALLOWED_HOSTS)

#if settings.BACKEND_CORS_ORIGINS:
#    app.add_middleware(
#        CORSMiddleware,
#        allow_origins=["*"],
#        #    str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
#        allow_credentials=True,
#        allow_methods=["*"],
#        allow_headers=["*"],
#    )

#app.add_middleware(ProjectMiddleware)

app.add_middleware(
    AuthenticationMiddleware,
    backend=SessionAuthBackend())

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE,
    max_age=settings.SESSION_EXPIRE_SECONDS,
    same_site=settings.SESSION_SAME_SITE,
    https_only=False)

# api-first-example
Reference example of API-first web application design


## About

This project is a reference implementation for a fundamental use case that I have had
in multiple projects now. The gist of the design problem is this:

A web API is required which is accessible both via programmatic interface (such as in
a script or a command-line program) as well as via javascript from a browser, thus also
enabling so-called "API-first" development of the user interface. The following basic
requirements are kept in mind:

 * The programmatic interface should be secured via a tokenization scheme (oauth2 is
   used).
 * The user interface authentication is arbitrary. Here, we use username/password, but
   the specifics of the web application might dictate something else.
 * The user interface provides a mechanism for creating/retrieving client keys for
   the programmatic API.

The chosen solution uses the following approach:

 * The programmatic API is built with FastAPI to take advantage of its documentation
   and validation features.
 * The web UI is built with Starlette for its simplicity.
 * Both applications use the same shared authorization backend, which uses Starlette
   middleware to assign authorization scopes as follows:

     - Client credentials requests utilize a bearer scheme and attaches api_auth to
       the scope.
     - Web requests use session cookies and attach both api_auth, and app_auth to the
       scope.
     - Both attach the authenticated user to the request, although this is likely
       optional for API requests, depending on the nature of resource ownership in the
       API.

Note: I find Starlette's middleware-based approach to auth much simpler than FastAPI's
dependency injection approach. So far, I have found the approach to work well with
either. In FastAPI, this approach requires passing the request to view functions via
dependency injection, and decorating the view with Starlette's `requires` decorator. E.g.:

```
@app.get("/tasks") # decorators must be in this order
@requires("api_auth")
async def get_tasks(request:Request):
    tasks = Task.for_user(request.user)
    return { "tasks": tasks }
```

Scopes are then applied as follows:

 * Web views requiring authentication will require app_auth
 * API handlers require api_auth

Finally, requests made via Javascript from the browser pass their cookie information.
This allows the browser to programatically access the API.


## Architectural notes

Both applications will need access to the same database, particularly the ouath client
and tokens tables. It is likely they will also both need access to users, or whatever
your resource-owning model is.


## Implementation notes

The "persistence" layer here is pretty crude, and meant for demo purposes only. Note
that for the most part things are held in memory and will tend to be cleared out if the
application is restarted. Although for developing convenience I am currently saving
client credentials via dbm.


## Programmatic Client

A CLI called tasks.py is provided to demonstrate API access. Use the client ID and
secret available in the /apps section of the UI for a user.


## Interactive Swagger docs

The FastAPI Swagger UI is available at http://localhost:5000/docs. You will first
need to authenticate in the web app (http://localhost:8000/login) in order to submit
auth-required requests via Swagger.

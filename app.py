import secrets
import pathlib
import os
import time
from typing import Optional


from fastapi.params import Form
from fastapi import FastAPI
from fastapi.param_functions import Cookie, Depends
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

SECRET_KEY = os.environ.get('SECRET_KEY', 'ef4ac4e2a33e4d9e0bb34200349e3544')

templates = Jinja2Templates(directory=pathlib.Path(__file__).parent / 'templates')


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}


class RequiresLoginException(Exception):
    pass



app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


# This is not really required for simple use case, but if we have a lot views 
# and want to protect them, a common redirect logic is convenient.
@app.exception_handler(RequiresLoginException)
async def exception_handler(*args, **kwargs) -> Response:
    return RedirectResponse(url='/', status_code=303)


def verify_session_id(request: Request, session_id: Optional[str] = Cookie(...)):
    """Verify the session_id in the fake db. 
    If it doesn't exist raise an exception to redirect to Login page"""
    print('cookies', session_id, request.session.get(session_id))
    if request.session.get(session_id) not in fake_users_db:
        # raise an exception so that we can redirect to the login
        # if there's no `session_id`` passed or wrong `session_id`` is given 
        raise RequiresLoginException


@app.get("/view", dependencies=[Depends(verify_session_id)])
def view(request: Request):
    print({"session": request.session, "cookie": request.cookies})
    # return JSONResponse({"session": request.session, "cookie": request.cookies})
    return templates.TemplateResponse("view.html", {
        "request": request, 
        "start_time": request.session.get('start_time', int(time.time()))
    })


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Get `username` and `password` from form data and authenticate the user
    If username doesn't exist, redirect to Login page.
    Else continue to `/view` page
    """
    # for simplicity we will only check the `username`` exists
    # we can add a `password` check if required
    if username not in fake_users_db:
        response = RedirectResponse(
            url="/",
            status_code=303
        )
        return response
    # why we need to set the status_code to `303` can be seen in the below git issue comment
    # https://github.com/encode/starlette/issues/632#issuecomment-527258349
    response = RedirectResponse(url="/view", status_code=303)
    session_id = secrets.token_hex(16)
    request.session.update({session_id: username, "start_time": int(time.time())})
    response.set_cookie('session_id', session_id)
    return response


@app.get("/logout", name="logout")
async def logout(request: Request):
    """Logout and redirect to Login screen"""
    print('here')
    request.session.clear()
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie('session_id', None)
    return response

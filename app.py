import secrets
import pathlib
import os
import time
from typing import Optional


from fastapi.params import Form
from fastapi import FastAPI
from fastapi.param_functions import Cookie, Depends
import socketio
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi_socketio import SocketManager


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
# socket_manager = SocketManager(app=app)
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*")
app.mount("/ws", socketio.ASGIApp(sio))
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=pathlib.Path(__file__).parent / 'templates'), name="static")


# This is not really required for simple use case, but if we have a lot views 
# and want to protect them, a common redirect logic is convenient.
@app.exception_handler(RequiresLoginException)
async def exception_handler(*args, **kwargs) -> Response:
    return RedirectResponse(url='/', status_code=303)


def verify_session_id(request: Request, session_id: Optional[str] = Cookie(...)):
    """Verify the session_id in the fake db. 
    If it doesn't exist raise an exception to redirect to Login page"""
    username = request.session.get(session_id)
    print('cookies', session_id, username)
    if username not in fake_users_db:
        # raise an exception so that we can redirect to the login
        # if there's no `session_id`` passed or wrong `session_id`` is given 
        raise RequiresLoginException
    return username


# @app.get("/view", dependencies=[Depends(verify_session_id)])
@app.get("/view")
async def view(request: Request, username: str = Depends(verify_session_id)):
    print({"session": request.session, "cookie": request.cookies})
    # return JSONResponse({"session": request.session, "cookie": request.cookies})
    await sio.emit('message', 'hello universe')
    return templates.TemplateResponse("view.html", {
        "request": request,
        "current_user": username,
        "start_time": request.session.get('start_time', int(time.time())),
        "PORT": os.environ.get('PORT', 8000)
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
    request.session.update({
        session_id: username, "start_time": int(time.time()), 
        "username": username, "sids": []
    })
    response.set_cookie('session_id', session_id)
    return response


@app.get("/logout", name="logout")
async def logout(request: Request, username: str = Depends(verify_session_id)):
    """Logout and redirect to Login screen"""
    print('here')
    request.session.clear()
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie('session_id', None)
    # await sio.emit('reply', 'bye bye')
    # await sio.emit('reply', username)
    # import asyncio
    # await asyncio.sleep(2)

    await sio.emit('logout', username)
    import asyncio
    # await asyncio.sleep(2)
    return response


# socket_manager.on('join')
# async def handle_join(sid, *args, **kwargs):
#     await socket_manager.emit('lobby', 'User joined')

# socket_manager.on('message')
# async def handle_join(sid, *args, **kwargs):
#     print(sid, args, kwargs)


# socket_manager.on('connect_error')
# async def handle_connect_error(*args, **kwargs):
#     print('connect error', args, kwargs)


@sio.event
async def connect(sid, environ):
    print("connect ", sid, environ)
    import pprint
    pprint.pprint(environ)
    session = environ['asgi.scope']['session']
    # await sio.emit('message', 'hello world')
    await sio.emit('new user', session)

@sio.event
async def chat_message(sid, data):
    print("message ", sid, data)
    await sio.emit('reply', room=sid)

@sio.event
async def message(sid, data):
    print("message ", sid, data)
    # await sio.emit('reply', room=sid)
    await sio.emit('message', data, room=sid)


@sio.event
def disconnect(sid):
    print('disconnect ', sid)
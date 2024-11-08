from fastapi import FastAPI, Request, Body, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_login.exceptions import InvalidCredentialsException

from datetime import timedelta

from models import Item, ToggleDeviceRequest, StatusDeviceRequest, SetDeviceRequest
from devices import Device
from auth import load_user, manager, NotAuthenticatedException
from dependencies import config

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


def exc_handler(request, exc):
    return RedirectResponse(url='/login')


app.add_exception_handler(NotAuthenticatedException, exc_handler)

templates = Jinja2Templates(directory="templates")

devices = {4: Device(4, 'Table Lamp', image='table_lamp.png'), 23: Device(23, 'Ceil Lamp', image='lustre.png')}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, user=Depends(manager)):
    return templates.TemplateResponse(
        request=request, name="home.html", context={"devices": devices}
    )


@app.post("/device")
def set_device(data: SetDeviceRequest, user=Depends(manager)):
    res = devices.get(data.pin).set(data.level)
    if not isinstance(res, int):
        raise HTTPException(status_code=418, detail=res.text)
    return {"level": res}


@app.put("/device")
def toggle_device(data: ToggleDeviceRequest, user=Depends(manager)):
    print(user)
    res = devices.get(data.pin).toggle()
    if not isinstance(res, int):
        raise HTTPException(status_code=418, detail=res.text)
    return {"level": res}


@app.get('/device')
def get_device_status(data: StatusDeviceRequest, user=Depends(manager)):
    res = devices.get(data.pin).status()
    if not isinstance(res, dict):
        raise HTTPException(status_code=418, detail=res.text)
    return res


@app.get("/users/me")
async def read_users_me(current_user=Depends(manager)):
    return current_user


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@app.post('/login')
def login(request: Request, data: OAuth2PasswordRequestForm = Depends()):
    username = data.username
    password = data.password
    user = load_user(username)
    if not user or password != user['password']:
        return templates.TemplateResponse(request=request, name="login.html",
                                          context={"error": "Invalid username or password"})
        # raise InvalidCredentialsException

    token = manager.create_access_token(data={'sub': username},
                                        expires=timedelta(minutes=config['jwt_expiration_time']))
    response = RedirectResponse(url="/", status_code=302)
    # manager.set_cookie(response, token)  # uses httponly flag
    response.set_cookie(key=manager.cookie_name, value=token)
    return response

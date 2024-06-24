from fastapi import FastAPI, Request, Body, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from typing import Annotated
from pydantic import BaseModel

from models import Item, ToggleDeviceRequest, StatusDeviceRequest, SetDeviceRequest
from devices import Device


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


devices={4:Device(4,'Table Lamp',image='table_lamp.png'),23:Device(23,'Ceil Lamp',image='lustre.png')}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):

    return templates.TemplateResponse(
        request=request, name="home.html", context={"devices":devices}
    )


@app.post("/device")
def toggle_device(data: SetDeviceRequest):
    res=devices.get(data.pin).set(data.level)
    if not isinstance(res, int):
        raise HTTPException(status_code=418, detail=res.text)
    return {"level": res}


@app.put("/device")
def toggle_device(data: ToggleDeviceRequest):
    res=devices.get(data.pin).toggle()
    if not isinstance(res, int):
        raise HTTPException(status_code=418, detail=res.text)
    return {"level": res}


@app.get('/device')
def get_device_status(data: StatusDeviceRequest):
    res=devices.get(data.pin).status()
    if not isinstance(res, dict):
        raise HTTPException(status_code=418, detail=res.text)
    return res


# @app.get("/items/{item_id}")
# async def read_item(item_id: str, q: str | None = None, t: int | None = None):
#     if q:
#         return {"item_id": item_id, "q": q, 't':t}
#     return {"item_id": item_id, 't':t}
#
#
# @app.post("/items")
# async def create_item(item: Item):
#     return item

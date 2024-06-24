from pydantic import BaseModel


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


class ToggleDeviceRequest(BaseModel):
    pin: int


class SetDeviceRequest(BaseModel):
    pin: int
    level: int


class StatusDeviceRequest(BaseModel):
    pin: int


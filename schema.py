from pydantic import BaseModel, ConfigDict

class ItemUpdate(BaseModel):
    name: str  | None = None
    stock: int | None = None


class ItemsCreate(BaseModel):
    name: str  | None = None
    stock: int | None = None


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    stock: int


class ItemListResponse(BaseModel):
    status: str
    data: list[ItemResponse]


class SingleItemResponse(BaseModel):
    status: str
    data: ItemResponse


class CreateItemResponse(BaseModel):
    status: str
    data: ItemResponse


class DeleteResponse(BaseModel):
    status: str
    item_id: int


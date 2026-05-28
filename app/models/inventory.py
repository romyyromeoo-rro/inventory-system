from sqlalchemy import Column, Integer, String
from app.databased import Base

class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, nullable=False)
    stock = Column(Integer, default=0)

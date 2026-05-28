from app.databased import engine, Base
from app.models.inventory import InventoryItem

Base.metadata.create_all(bind=engine)

print("Tables created successfully")

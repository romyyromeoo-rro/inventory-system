from app.databased import SessionLocal
from app.models.inventory import InventoryItem

db = SessionLocal()

item = db.query(InventoryItem).filter(
    InventoryItem.item_name == "indomie"
).first()

db.delete(item)

db.commit()

print("item Deleted")

db.close()

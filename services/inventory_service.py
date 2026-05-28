import time
import json
from fastapi import HTTPException
from database import get_connection
from sqlalchemy.orm import Session
from app.models.inventory import InventoryItem
from repository.inventory_repo import *
from services.audit_service import log_action_service
from cache import get_cache, set_cache
from services.task_queue import push_task
from redis_client import redis_client
from core.config import config



LAST_UPDATE = {}
CACHE_KEY = config.CACHE_KEY


def get_item_service():
    cached = redis_client.get(CACHE_KEY)

    if cached:
        print("⚡ CACHE HIT")
        return json.loads(cached)

    print("🐢 CACHE MISS")
    print("🐘 FROM DB")

    conn = get_connection()

    try:
        rows = get_all_items(conn)


        items = []
        for row in rows:
            items.append({
                "id": row[0],
                "name": row[1],
                "stock": row[2]
            })

        set_cache(CACHE_KEY, items, ttl=60)

        return items


    finally:
        conn.close()


def get_item_by_id_service(item_id):
    cache_key = f"item_{item_id}"

    cached = redis_client.get(cache_key)

    if cached:
        print("⚡ CACHE HIT (ITEM)")
        return json.loads(cached)

    print("🐢 CACHE MISS (ITEM)")
    print("🐘 FROM DB")

    item = db.query(InventoryItem).filter(
        InventoryItem.id == item_id
    ).first()

    if item is None:
        raise HTTPException(404, "item not found")

    item_data = {
        "id": item.id,
        "name": item.item_name,
        "stock": item.stock
    }

    redis_client.set(cache_key, json.dumps(item_data), ex=60)

    return item_data


def create_item_service(
    db: Session,
    new_item,
    request
):
    if new_item.stock < 0:
        raise Exception("Stock cannot be negative")

    existing = db.query(InventoryItem).filter(
    InventoryItem.item_name == new_item.name
    ).first()

    if existing:
        raise ValueError("Item already exists")

    item = InventoryItem(
       item_name=new_item.name,
       stock=new_item.stock
    )

    db.add(item)

    db.commit()

    db.refresh(item)

    redis_client.delete("items_list")

    print("🧹 CACHE CLEARED")

    push_task({
        "username": username,
        "action": "CREATE ITEM",
        "item_id": item_id,
        "item_name": new_item.name,
        "old_stock": 0,
        "new_stock": new_item.stock,
        "ip_address": request.client.host,
        "endpoint": str(request.url)
    })

    return {
        "status": "Success",
        "data": {
            "id": item.id,
            "name": item.item_name,
            "stock": item.stock
        }
    }



def update_item_service(
    db: Session,
    item_id,
    new_data,
    request
):
    item = db.query(InventoryItem).filter(
        InventoryItem.id == item_id
    ).first()

    if not item:
        raise Exception("NOT FOUND")

    old_id = item.id
    old_name = item.item_name
    old_stock = item.stock

    new_name = (
        new_data.name
        if new_data.name is not None else old_name
    )

    new_stock = (
        new_data.stock
        if new_data.stock is not None else old_stock
    )

    if new_name == old_name and new_stock == old_stock:
        return {"message": "No changes"}


        #key = f"{user['sub']}_{item_id}"
        #now = time.time()

        #if key in LAST_UPDATE and now - LAST_UPDATE[key] < 2:
            #raise Exception("TOO FAST")

        #LAST_UPDATE[key] = now

    item.item_name = new_name
    item.stock = new_stock

    db.commit()

    db.refresh(item)

    print("🧹 TRY DELETE items_list")
    deleted = redis_client.delete("items_list")
    print("🧹 DELETED COUNT:", deleted)
    print("🧹 TRY DELETE item_id")
    delete = redis_client.delete(f"item_{item_id}")
    print("🧹 DELETED COUNT:", delete)

    push_task({
        "username": username,
        "action": "UPDATE ITEM",
        "item_id": item_id,
        "item_name": item_name,
        "old_stock": old_stock,
        "new_stock": new_stock,
        "ip_address": request.client.host,
        "endpoint": str(request.url)

    })


    return {
       "status": "Item updated",
       "data": {
            "id": item_id,
            "name": item.item_name,
            "old": old_stock,
            "new": new_stock
       }
    }




def delete_item_service(
    db: Session,
    item_id,
    request
):
    #if user['role'] != "admin":
        #return "FORBIDDEN"
    item = db.query(InventoryItem).filter(
        InventoryItem.id == item_id
    ).first()

    if item is None:
        raise HTTPException(404, "item not found")

    item_name = item.item_name
    old_stock = item.stock

    db.delete(item)

    db.commit()

    redis_client.delete("items_list")
    redis_client.delete(f"item_{item_id}")

    print("🧹 CACHE CLEARED")

    push_task({
        "username": username,
        "action": "DELETE ITEM",
        "item_id": item_id,
        "item_name": item_name,
        "old_stock": old_stock,
        "new_stock": 0,
        "change": 0 - old_stock,
        "ip_address": request.client.host,
        "endpoint": str(request.url)
    })


    return {
         "status": "Success",
         "message": "Item Deleted",
         "item_id": item_id
    }

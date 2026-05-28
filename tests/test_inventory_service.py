from services.inventory_service import get_item_service

def test_get_items_returns_list():
    items = get_item_service()

    assert isinstance(items, list)

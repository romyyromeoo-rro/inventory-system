from fastapi.testclient import TestClient
from main import app

client = TestClient(app)



def get_token():
    response = client.post(
        "/login",
        params = {
            "username": "admin",
            "password": "admin123"
        }
    )

    data = response.json()
    return data["access_token"]




def test_get_items_endpoint():
    response = client.get("/items")

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert isinstance(data["items"], list)



def test_create_item():
    token = get_token()

    response = client.post(
        "/items",
        headers={
            "Authorization":f"Bearer {token}"
        },
        json={
            "name": "TestItem",
            "stock": 50
        }
    )

    print(response.json())
    assert response.status_code == 200



def test_update_item():
    token = get_token()

    response = client.put(
        "/items/2",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Jam Test",
            "stock": 35
        }
    )


    assert response.status_code == 200

    data = response.json()

    assert (
         data["status"] == "Item updated"
         or data["message"] == "No changes"
    )

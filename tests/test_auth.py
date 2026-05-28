from fastapi.testclient import TestClient
from main import app

client = TestClient(app)



def test_login_success():
    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"




def test_login_wrong_password():
    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "wrongpass"
        }
    )

    assert response.status_code == 401




def test_protected_without_token():
    response = client.get("/protected")

    assert response.status_code == 401




def test_logout_blacklist_token():
    login = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login.status_code == 200

    body = login.json()
    assert "access_token" in body

    token = body["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    logout = client.post(
        "/logout",
        headers=headers
    )

    assert logout.status_code == 200

    protected = client.get(
        "/protected",
        headers=headers
    )

    assert protected.status_code == 401



def test_refresh_token():
    login = client.post(
        "/login",
        data= {
            "username": "admin",
            "password": "admin123"
        }
    )

    refresh_token = login.json()["refresh_token"]

    response = client.post(
        f"/refresh?refresh_token={refresh_token}"
    )

    assert response.status_code == 200

    body = response.json()

    assert "access_token" in body
    assert body["token_type"] == "bearer"




def test_access_token_cannot_refresh():
    login = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    access_token = (
        login.json()["access_token"]
    )

    response = client.post(
        f"/refresh?refresh_token={access_token}"
    )

    assert response.status_code == 401



def test_refresh_token_rotation():
    login = client.post(
        "/login",
        data ={
            "username": "admin",
            "password": "admin123"
        }
    )

    old_refresh = (
        login.json()["refresh_token"]
    )

    first = client.post(
        f"/refresh?refresh_token={old_refresh}"
    )

    assert first.status_code == 200

    new_refresh = (
        first.json()["refresh_token"]
    )

    assert new_refresh != old_refresh

    reuse = client.post(
        f"/refresh?refresh_token={old_refresh}"
    )

    assert reuse.status_code == 401



#def test_staff_cannot_delete(staff_token):
    #response = client.delete(
        #"/items/1",
        #headers= {
            #"Authorization": f"Bearer {staff_token}"
        #}
    #)
    #assert response.status_code == 403



#def test_creste_pushes_log():
    #response = client.post(
        #"/items",
        #json={"Name": "Milk", "stock":10}
    #)

    #assert response.status_code == 200


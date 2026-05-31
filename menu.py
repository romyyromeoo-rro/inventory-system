from inputimeout import inputimeout, TimeoutOccurred
from database import get_connection
from auth import login, create_user
from inventory_manager import *
from audit import *
from datetime import datetime, timedelta
from auth.token_service import create_access_token, verify_token, verify_jwt


SESSION_TIMEOUT = 1
INPUT_TIMEOUT = 30


def is_session_expired(session):
    return datetime.now() - session["last_activity"] > timedelta(minutes=SESSION_TIMEOUT)


def validate_session(session):
    if not session or "token" not in session:
        return False


    payload = verify_token(session["token"])

    if not payload:
        return False

    return payload



def update_activity(session):
    session["last_activity"] = datetime.now()



def is_admin(role):
    return role == 'admin'



def is_staff(role):
    return role == 'staff'



def show_menu(conn, session):
    payload = validate_session(session)


    if not payload:
        print("🚫 Invalid / Expired token.")
        return


    current_user = payload.get("sub")
    role = payload.get("role")

    while True:
        if is_session_expired(session):
            print("⏳ Session expired. Auto logout.")
            break


        print(f"\nLogin sebagai: {current_user} ({role})")

        print("\n=== MENU INVENTORY ===")
        print("1. Create User")
        print("2. Tambah Barang")
        print("3. Lihat Semua Barang")
        print("4. Update Stock")
        print("5. Delete Barang")
        print("6. Cari Barang")
        print("7. Lihat Audit Log")
        print("8. Logout")

        try:
            pilihan = inputimeout(prompt="Choose: ", timeout=INPUT_TIMEOUT)

        except TimeoutOccurred:
            print("⚠ Tidak ada input. Silahkan pilih menu.")
            continue


        update_activity(session)

        if pilihan == "1":
            if session["role"] != "admin":
                print("❌ Access Denied. Only Admin Can Create Users.!")
            else:
                create_user(conn)

        elif pilihan == "2":
            add_item(conn, current_user)

        elif pilihan == "3":
            view_items(conn, current_user)

        elif pilihan == "4":
            update_stock(conn, current_user)

        elif pilihan == "5":
            if not is_admin(role):
                print("❌ Access Denied. Only Admin Can delete the items.!")
            else:
                delete_items(conn, current_user, role)

        elif pilihan == "6":
            search_item(conn)

        elif pilihan == "7":
            if not is_admin(role):
                print("❌ Access Denied. Only admin can see the Logs.")
            else:
                view_logs(conn)


        elif pilihan == "8":
            print("Logout Berhasil")
            session = None
            break


        else:
            print("Menu Tidak Valid!")

    print("GoodBye... Have a nice day")

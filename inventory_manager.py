from services.inventory_service import update_item_service
from database import get_connection


def show_dashboard(conn):
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM items")
    total_items = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(stock) FROM items")
    total_stock = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM items WHERE stock <= 5")
    low_stock = cursor.fetchone()[0]

    print("\n==== INVENTORY DASHBOARD ====")
    print(f"Total Items           :{total_items}")
    print(f"Total Stock           :{total_stock}")
    print(f"Low Stock Items       :{low_stock}")



def log_action(conn, username, action, item_name):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO audit_log (username, action, item_name) VALUES (?, ?, ?)", (username, action, item_name))
    conn.commit()


def check_low_stock(conn):
    cursor = conn.cursor()

    cursor.execute("SELECT name, stock FROM items WHERE stock <= 5")
    items = cursor.fetchall()
    if items:
        print("\n⚠ LOW STOCK WARNING")
        print("---------------------------")

        for item in items:
            print(f"{item[0]} : {item[1]}")



def views_items():
    items = get_all_items_from_db()
    return items



def view_items(conn, username):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()

    print("\n=== DAFTAR BARANG ===")
    for item in items:
        print(f"ID: {item[0]} | Name: {item[1]} | Stock: {item[2]}")



def add_item(conn, username):
    item_name = input("ID Barang: ")
    stock = input("Stock Baru: ")

    cursor = conn.cursor()
    cursor.execute("INSERT INTO items (name, stock) VALUES (?, ?)", (item_name, stock))
    conn.commit()

    log_action(conn, username, "ADD ITEM", item_name)
    print("Barang Berhasil Ditambahkan.")



def update_stock_api(username):
    conn = get_connection()

    item_id = input("ID BARANG: ")
    new_stock = input("STOCK BARU: ")

    result = update_stock_service(conn, username, item_id, new_stock, log_action)

    if result == "NOT FOUND":
        print("Barang Tidak Ditemukkan!")

    else:
        print("Stock Berhasil Diupdate!")


#def update_stock(conn, username):
    item_id = input("ID Barang: ")
    new_stock = input("Stock Baru: ")

    cursor = conn.cursor()

    cursor.execute("SELECT name, stock FROM items WHERE id = ?", (item_id,))
    result = cursor.fetchone()

    if not result:
        print("Barang Tidak Ditemukan!.")
        return

    item_name = result[0]
    old_stock = result[1]

    cursor.execute("UPDATE items SET stock=? WHERE id=?", (new_stock, item_id))
    conn.commit()

    log_action(conn, username, "UPADTE STOCK", f"{item_name}: {old_stock} -> {new_stock}")
    print("Stock Berhasil Diupdate.")



def delete_item(conn, current_user, role):
    if role != "admin":
        print("❌ Unauthorized action!")
        return

    item_id = input("ID Barang Yang Akan Dihapus: ")

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM items WHERE id=?", (item_id,))
    result = cursor.fetchone()

    if not result:
        print("Barang Tidak Ditemukan!.")
        return

    item_name = result[0]
    cursor.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()
    log_action(conn, current_user, "DELETE ITEM", item_name)

    print("Barang Berhasil Dihapus.")



def search_item(conn):
    keyword = input("Keyword: ")

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE name LIKE ?", ('%' + keyword + '%',))

    results = cursor.fetchall()

    print("\n=== HASIL PENCARIAN ===")
    for item in results:
        print(f"ID: {item[0]} | Name: {item[1]} | Stock: {item[2]}")



def view_logs(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, action, item_name, timestamp FROM audit_log")
    logs = cursor.fetchall()
    print("\n-----AUDIT LOG-----")
    print("ID | USER | ACTION | ITEM | TIME")
    print("-"*45)

    for log in logs:
        print(f"{log[0]} | {log[1]} | {log[2]} | {log[3]} | {log[4]}")

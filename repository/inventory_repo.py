def get_all_items(conn):
    cursor = conn.cursor()
    cursor.execute(""" SELECT id, name, stock FROM items""")
    return cursor.fetchall()



def get_item_by_id(conn, item_id):
    cursor = conn.cursor()
    cursor.execute(""" SELECT id, name, stock FROM items
        WHERE id = ?""", (item_id,))
    return cursor.fetchone()


def get_item_by_name(conn, item_name):
    cursor = conn.cursor()
    cursor.execute(""" SELECT id, name, stock FROM items
        WHERE name = ?""", (item_name,))



def create_item(conn, item_name, stock):
    cursor = conn.cursor()
    cursor.execute(""" INSERT INTO items (name, stock) 
        VALUES (?, ?)""", (item_name, stock))

    conn.commit()


def update_item_by_id(conn, item_id, name, stock):
    cursor = conn.cursor()
    cursor.execute(""" UPDATE items SET name = ?, stock= ? WHERE
        id = ?""", (name, stock, item_id))
    conn.commit()



def delete_item_by_id(conn, item_id):
    cursor = conn.cursor()
    cursor.execute(""" DELETE FROM items WHERE id = ?""", (item_id,))
    conn.commit()


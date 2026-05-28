def log_action_service(
    conn,
    username,
    action,
    item_id=None,
    item_name=None,
    old_stock=None,
    new_stock=None,
    ip_address=None,
    endpoint=None
):
    cursor = conn.cursor()

    cursor.execute(""" INSERT INTO audit_log(username,
        action, item_id, item_name, old_stock, new_stock,
        ip_address, endpoint) VALUES (?, ?, ?, ?, ?,
        ?, ?, ?)""", (username,
                      action,
                      item_id,
                      item_name,
                      old_stock,
                      new_stock,
                      ip_address,
                      endpoint
    ))

    conn.commit()


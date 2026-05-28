                                   Table "public.inventory_items"
  Column   |       Type        | Collation | Nullable |                   Default                   
-----------+-------------------+-----------+----------+---------------------------------------------
 id        | integer           |           | not null | nextval('inventory_items_id_seq'::regclass)
 item_name | character varying |           | not null | 
 stock     | integer           |           |          | 
Indexes:
    "inventory_items_pkey" PRIMARY KEY, btree (id)
    "ix_inventory_items_id" btree (id)

